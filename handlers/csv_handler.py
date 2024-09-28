import csv
import logging
from telegram import Update
from telegram.ext import ContextTypes
from helpers.db import users_collection
from config import ADMIN_ID

UPLOAD_CSV, CHOOSE_DESTINATION = range(2)

async def upload_csv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    user_info = users_collection.find_one({'user_id': user_id})

    

    if user_info or user_id == ADMIN_ID:

        await update.message.reply_text(
        
         "📂 ᴛᴏ ᴜᴘʟᴏᴀᴅ ʏᴏᴜʀ ᴄꜱᴠ ꜰɪʟᴇ ꜰᴏʀ ᴍᴄQ ᴄᴏɴᴠᴇʀꜱɪᴏɴ, ᴘʟᴇᴀꜱᴇ ᴇɴꜱᴜʀᴇ ɪᴛ ᴍᴇᴇᴛꜱ ᴛʜᴇ ꜰᴏʟʟᴏᴡɪɴɢ ʀᴇQᴜɪʀᴇᴍᴇɴᴛꜱ:  \n"
    "👉 ꜰᴏʀᴍᴀᴛ: \"Question\", \"Option A\", \"Option B\", \"Option C\", \"Option D\", \"Answer\", \"Description\".  \n"
    "👉 ᴛʜᴇ \"ᴀɴꜱᴡᴇʀ\" ꜱʜᴏᴜʟᴅ ʙᴇ ɪɴ ᴀ, ʙ, ᴄ, ᴅ ꜰᴏʀᴍᴀᴛ.  \n"
    "👉 ᴛʜᴇ \"ᴅᴇꜱᴄʀɪᴘᴛɪᴏɴ\" ɪꜱ ᴏᴘᴛɪᴏɴᴀʟ. ɪꜰ ɴᴏᴛ ᴘʀᴏᴠɪᴅᴇᴅ, ɪᴛ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ꜰɪʟʟᴇᴅ.  \n"
    "ᴇxᴀᴍᴘʟᴇ ᴄꜱᴠ ꜰᴏʀᴍᴀᴛ: \n"
    "[Download Example CSV](https://t.me/How_To_Google/10) \n"
            
        )

        return UPLOAD_CSV

    else:

        await update.message.reply_text("You are not authorized to use this bot. Please contact the admin.")

        return ConversationHandler.END

# Handle CSV file upload



async def handle_csv_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

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

async def choose_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    choice = query.data

    if choice == 'bot':
        chat_id = query.message.chat_id
        questions = context.user_data.get('questions', [])
        await send_all_polls(chat_id, context, questions)
        await query.edit_message_text("Quizzes have been sent to the bot.")
        return ConversationHandler.END

    elif choice == 'channel':
        user_info = users_collection.find_one({'user_id': user_id})
        if 'channels' in user_info and user_info['channels']:
            if len(user_info['channels']) == 1:
                channel_id = user_info['channels'][0]
                questions = context.user_data.get('questions', [])
                await send_all_polls(channel_id, context, questions)
                await query.edit_message_text(f"Quizzes have been sent to {channel_id}.")
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
    await send_all_polls(channel_id, context, questions)
    await query.edit_message_text(text=f"Quizzes have been sent to {channel_id}.")
    return ConversationHandler.END
