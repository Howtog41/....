import csv
import logging
import asyncio  # Make sure to import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from helpers.db import users_collection
from config import ADMIN_ID
from telegram.error import RetryAfter
from datetime import datetime
UPLOAD_CSV, CHOOSE_DESTINATION = range(2)
user_state = {}


async def upload_csv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_info = users_collection.find_one({'user_id': user_id})
    now = datetime.now()

    if user_id == ADMIN_ID:
        pass_access = True
    elif user_info and user_info.get('authorized', False):
        expires_on = user_info.get('expires_on')
        pass_access = expires_on and expires_on > now
    else:
        pass_access = False

    if pass_access:
        user_state[user_id] = {'collecting': True, 'title': False}
        await update.message.reply_text(
            "📂 ᴛᴏ ᴜᴘʟᴏᴀᴅ ʏᴏᴜʀ ᴄꜱᴠ ꜰɪʟᴇ ꜰᴏʀ ᴍᴄQ ᴄᴏɴᴠᴇʀꜱɪᴏɴ, ᴘʟᴇᴀꜱᴇ ᴇɴꜱᴜʀᴇ ɪᴛ ᴍᴇᴇᴛꜱ ᴛʜᴇ ꜰᴏʟʟᴏᴡɪɴɢ ʀᴇQᴜɪʀᴇᴍᴇɴᴛꜱ:\n\n"
            "Copy the below format and paste it into any AI bot to convert your questions into CSV.\n"
            "```\n"
            "👉 ꜰᴏʀᴍᴀᴛ: \n"
            "\"Question\", \"Option A\", \"Option B\", \"Option C\", \"Option D\", \"Answer\", \"Description\"\n"
            "👉 ᴛʜᴇ \"ᴀɴꜱᴡᴇʀ\" ꜱʜᴏᴜʟᴅ ʙᴇ ɪɴ A, B, C, D ꜰᴏʀᴍᴀᴛ.\n"
            "👉 ᴛʜᴇ \"ᴅᴇꜱᴄʀɪᴘᴛɪᴏɴ\" ɪꜱ ᴏᴘᴛɪᴏɴᴀʟ. ɪꜰ ɴᴏᴛ ᴘʀᴏᴠɪᴅᴇᴅ, ɪᴛ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ ꜰɪʟʟᴇᴅ.\n\n"
            "```\n"
            "📥 Example CSV: [Download](https://t.me/How_To_Google/10)",
            parse_mode='Markdown'
        )
        keyboard = [
            [InlineKeyboardButton("🔁 Use AI Bot for Format", url="https://t.me/gpt3_unlim_chatbot")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        
        return UPLOAD_CSV

    else:

        await update.message.reply_text("You are not authorized to use this bot. Please contact the admin.")

        return ConversationHandler.END



# Handle CSV file upload



async def handle_csv_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # ✅ Ensure user is in correct state
    if not user_state.get(user_id, {}).get('collecting', False):
        await update.message.reply_text(
            "❌ Please use /uploadcsv command first before sending a CSV file."
        )
        return ConversationHandler.END

    logging.info(f"Handling CSV upload for user: {user_id}")

    if user_id == ADMIN_ID or users_collection.find_one({'user_id': user_id}):
        try:
            file = await update.message.document.get_file()
            file_path = f"{file.file_id}.csv"
            logging.info(f"Downloading CSV file to: {file_path}")
            await file.download_to_drive(file_path)
            
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                questions = list(reader)

            logging.info(f"CSV file processed with {len(questions)} questions.")
            
            context.user_data['questions'] = questions

            keyboard = [
                [InlineKeyboardButton("Bot", callback_data='bot')],
                [InlineKeyboardButton("Channel", callback_data='channel')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "Do you want to upload these quizzes to the bot or forward them to a channel?",
                reply_markup=reply_markup
            )

            return CHOOSE_DESTINATION

        except Exception as e:
            logging.error(f"Error processing CSV file: {e}")
            await update.message.reply_text("There was an error processing the file. Please try again.")
            return ConversationHandler.END

    else:
        await update.message.reply_text("You are not authorized to use this bot. Please contact the admin.")
        return ConversationHandler.END


#yha se hendler add krna hai 


async def send_message_with_retry(bot, chat_id, text):
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    except RetryAfter as e:
        print(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
        await asyncio.sleep(e.retry_after)
        await send_message_with_retry(bot, chat_id, text)

async def send_all_polls(chat_id, context, questions):
    for question in questions:
        try:
            await context.bot.send_poll(
                chat_id=chat_id,
                question=question["text"],
                options=question["options"],
                is_anonymous=False
            )
            await asyncio.sleep(2)  # Small delay between polls to avoid rate limits
        except RetryAfter as e:
            print(f"Flood control exceeded. Retrying in {e.retry_after} seconds.")
            await asyncio.sleep(e.retry_after)
        except Exception as e:
            print(f"Error sending poll: {e}")

async def choose_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    choice = query.data

    if choice == 'bot':
        chat_id = query.message.chat_id
        questions = context.user_data.get('questions', [])

        # Send polls in batches
        total_polls = len(questions)
        batch_size = 19
        sent_polls = 0

        for i in range(0, total_polls, batch_size):
            batch = questions[i:i + batch_size]
            await send_all_polls(chat_id, context, batch)
            sent_polls += len(batch)
            await send_message_with_retry(context.bot, chat_id, f"{sent_polls} polls have been sent to the bot.")

            # Wait for 30 seconds before sending the next batch
            if i + batch_size < total_polls:
                await asyncio.sleep(30)

        await send_message_with_retry(context.bot, chat_id, f"Total of {sent_polls} quizzes have been sent to the bot.")
        return ConversationHandler.END

    elif choice == 'channel':
        user_info = users_collection.find_one({'user_id': user_id})
        if 'channels' in user_info and user_info['channels']:
            if len(user_info['channels']) == 1:
                channel_id = user_info['channels'][0]
                questions = context.user_data.get('questions', [])

                # Send polls in batches to the channel
                total_polls = len(questions)
                batch_size = 19
                sent_polls = 0

                for i in range(0, total_polls, batch_size):
                    batch = questions[i:i + batch_size]
                    await send_all_polls(channel_id, context, batch)
                    sent_polls += len(batch)
                    await send_message_with_retry(context.bot, channel_id, f"{sent_polls} polls have been sent to {channel_id}.")

                    # Wait for 30 seconds before sending the next batch
                    if i + batch_size < total_polls:
                        await asyncio.sleep(30)

                await send_message_with_retry(context.bot, channel_id, f"Total of {sent_polls} quizzes have been sent to {channel_id}.")
                return ConversationHandler.END
            else:
                keyboard = [
                    [InlineKeyboardButton(channel, callback_data=channel) for channel in user_info['channels']]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("Choose a channel:", reply_markup=reply_markup)
                return CHOOSE_CHANNEL
        else:
            await query.edit_message_text("No channels are set. Please set a channel using /setchannel <channel_id>.")
            return ConversationHandler.END

    else:
        await query.edit_message_text("Invalid choice. Please select 'bot' or 'channel'.")
        return CHOOSE_DESTINATION

async def channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    channel_id = query.data
    questions = context.user_data.get('questions', [])

    # Send polls in batches to the selected channel
    total_polls = len(questions)
    batch_size = 19
    sent_polls = 0

    for i in range(0, total_polls, batch_size):
        batch = questions[i:i + batch_size]
        await send_all_polls(channel_id, context, batch)
        sent_polls += len(batch)
        await send_message_with_retry(context.bot, channel_id, f"{sent_polls} polls have been sent to {channel_id}.")

        # Wait for 30 seconds before sending the next batch
        if i + batch_size < total_polls:
            await asyncio.sleep(30)

    await send_message_with_retry(context.bot, channel_id, f"Total of {sent_polls} quizzes have been sent to {channel_id}.")
    return ConversationHandler.END
    
