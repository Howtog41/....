from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from helpers.db import users_collection
import asyncio
from math import ceil

ASK_TAG = 101
CHOOSE_CHANNEL = 102
CHOOSE_DESTINATION = 103

async def choose_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    choice = query.data

    context.user_data["destination_choice"] = choice  # Save for use after tag input

    await query.edit_message_text(
        "📢 Kya aap kisi tag/channel name ko MCQ ke description me jodna chahte hain?\n\n"
        "Udaaharan: `@SecondCoaching`, `@howtogoogle`, ya agar skip karna ho to `skip` likhein.",
        parse_mode="Markdown"
    )
    return ASK_TAG

async def ask_custom_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tag = update.message.text.strip()
    if tag.lower() != "skip":
        context.user_data["custom_tag"] = tag if tag.startswith('@') else f"@{tag}"
        await update.message.reply_text(f"✅ Tag set ho gaya: `{context.user_data['custom_tag']}`", parse_mode="Markdown")
    else:
        context.user_data["custom_tag"] = None
        await update.message.reply_text("❎ Koi tag nahi joda jayega.")

    choice = context.user_data.get("destination_choice")
    user_id = update.effective_user.id
    questions = context.user_data.get('questions', [])

    if choice == 'bot':
        await send_questions(update.effective_chat.id, context, questions)
        await update.message.reply_text("📩 Quizzes have been sent to the bot.")
        return ConversationHandler.END

    elif choice == 'channel':
        user_info = users_collection.find_one({'user_id': user_id})
        if 'channels' in user_info and user_info['channels']:
            if len(user_info['channels']) == 1:
                channel_id = user_info['channels'][0]
                await send_all_polls(channel_id, context, questions)
                await update.message.reply_text(f"📩 Quizzes have been sent to {channel_id}.")
                return ConversationHandler.END
            else:
                keyboard = [[InlineKeyboardButton(channel, callback_data=channel)] for channel in user_info['channels']]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("Choose a channel:", reply_markup=reply_markup)
                return CHOOSE_CHANNEL
        else:
            await update.message.reply_text("❌ No channels found. Please use /setchannel.")
            return ConversationHandler.END

async def channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    channel_id = query.data
    questions = context.user_data.get('questions', [])
    await send_all_polls(channel_id, context, questions)
    await query.edit_message_text(text=f"Quizzes have been sent to {channel_id}.")
    return ConversationHandler.END

async def send_all_polls(chat_id, context: ContextTypes.DEFAULT_TYPE, questions, use_batches=True):
    custom_tag = context.user_data.get("custom_tag", "@SecondCoaching")

    if use_batches:
        chunk_size = 15
        total_batches = ceil(len(questions) / chunk_size)
        for batch_num in range(total_batches):
            start = batch_num * chunk_size
            end = start + chunk_size
            current_batch = questions[start:end]

            msg = await context.bot.send_message(chat_id=chat_id, text=f"📦 Sending batch {batch_num+1}/{total_batches}...")
            await asyncio.sleep(2)
            await context.bot.delete_message(chat_id=chat_id, message_id=msg.message_id)

            await send_questions(chat_id, context, current_batch)

            countdown = 30
            msg = await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Batch {batch_num+1} complete.\n⏳ Deleting in {countdown} seconds..."
            )

            for i in range(countdown - 1, 0, -1):
                await asyncio.sleep(2)
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=msg.message_id,
                        text=f"✅ Batch {batch_num+1} complete.\n⏳ Deleting in {i} seconds..."
                    )
                except:
                    pass

            await asyncio.sleep(1)
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
            except:
                pass

async def send_questions(chat_id, context: ContextTypes.DEFAULT_TYPE, questions):
    answer_mapping = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    max_question_length = 255
    max_option_length = 100
    max_description_length = 200
    custom_tag = context.user_data.get("custom_tag", "@SecondCoaching")

    for question in questions:
        try:
            text = question.get('Question', '').strip()
            options = [
                question.get('Option A', '').strip(),
                question.get('Option B', '').strip(),
                question.get('Option C', '').strip(),
                question.get('Option D', '').strip(),
            ]
            correct_option = question.get('Answer', '').strip()
            correct_option_id = answer_mapping.get(correct_option.upper(), None)
            description = question.get('Description', '').strip()

            missing_data = False
            if not text:
                missing_data = True
            for option in options:
                if not option:
                    missing_data = True
            if correct_option_id is None:
                missing_data = True
            if missing_data:
                message_text = (
                    f"Question: {text if text else '[Missing]'}\n\n"
                    f"Option A: {options[0] if options[0] else '[Missing]'}\n"
                    f"Option B: {options[1] if options[1] else '[Missing]'}\n"
                    f"Option C: {options[2] if options[2] else '[Missing]'}\n"
                    f"Option D: {options[3] if options[3] else '[Missing]'}\n"
                    f"Answer: {correct_option if correct_option else '[Missing]'}\n\n"
                    "❗ Is MCQ me option ya answer missing hai. Kripya sudhaar kar punah upload karein."
                )
                await context.bot.send_message(chat_id=chat_id, text=message_text)
                continue

            if custom_tag and custom_tag not in description:
                description = f"{description} {custom_tag}" if description else custom_tag
            if len(description) > max_description_length:
                description = description[:max_description_length].rsplit(' ', 1)[0] + "..."

            if len(text) <= max_question_length and all(len(option) <= max_option_length for option in options):
                await context.bot.send_poll(
                    chat_id=chat_id,
                    question=text,
                    options=options,
                    type='quiz',
                    correct_option_id=correct_option_id,
                    explanation=description,
                    is_anonymous=True
                )
            else:
                message_text = (
                    f"🆀🆄🅴🆂🆃🅸🅾🅽: {text}\n\n"
                    f"🅾🅿🆃🅸🅾🅽 A: {options[0]}\n"
                    f"🅾🅿🆃🅸🅾🅽 B: {options[1]}\n"
                    f"🅾🅿🆃🅸🅾🅽 C: {options[2]}\n"
                    f"🅾🅿🆃🅸🅾🅽 D: {options[3]}"
                )
                await context.bot.send_message(chat_id=chat_id, text=message_text)
                await context.bot.send_poll(
                    chat_id=chat_id,
                    question="Upr diye gye Question ka Answer kya hoga?👆",
                    options=['A', 'B', 'C', 'D'],
                    type='quiz',
                    correct_option_id=correct_option_id,
                    explanation=description,
                    is_anonymous=True
                )

            await asyncio.sleep(1)
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ CSV me kuch gadbadi hai.")
            continue
