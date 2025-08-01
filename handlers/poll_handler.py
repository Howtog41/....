from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from helpers.db import users_collection
import asyncio
async def choose_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    choice = query.data

    if choice == 'bot':
        chat_id = query.message.chat_id
        questions = context.user_data.get('questions', [])
        await send_all_poll(chat_id, context: ContextTypes.DEFAULT_TYPE, questions)
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

import asyncio
from math import ceil

async def send_all_polls(chat_id, context: ContextTypes.DEFAULT_TYPE, questions):
    answer_mapping = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    max_question_length = 255
    max_option_length = 100
    max_description_length = 200

    chunk_size = 15
    total_batches = ceil(len(questions) / chunk_size)

    for batch_num in range(total_batches):
        start = batch_num * chunk_size
        end = start + chunk_size
        current_batch = questions[start:end]

        msg = await context.bot.send_message(chat_id=chat_id, text=f"📦 Sending batch {batch_num+1}/{total_batches}...")

        # 5 second rukna
        await asyncio.sleep(2)

        # Message delete karna
        await context.bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
        for question in current_batch:
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

                # Missing data check
                missing_data = False
                missing_elements = []
                if not text:
                    missing_elements.append("Question")
                    missing_data = True
                for index, option in enumerate(options):
                    if not option:
                        missing_elements.append(f"Option {chr(65 + index)}")
                        missing_data = True
                if correct_option_id is None:
                    missing_elements.append("Answer")
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

                # Add @SecondCoaching if not present
                if '@SecondCoaching' not in description:
                    description = f"{description} @SecondCoaching" if description else "@SecondCoaching"

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
                    # Send text-based question
                    message_text = (
                        f"🆀🆄🅴🆂🆃🅸🅾🅽: {text}\n\n"
                        f"🅾🅿🆃🅸🅾🅽 A: {options[0]}\n"
                        f"🅾🅿🆃🅸🅾🅽 B: {options[1]}\n"
                        f"🅾🅿🆃🅸🅾🅽 C: {options[2]}\n"
                        f"🅾🅿🆃🅸🅾🅽 D: {options[3]}"
                    )
                    await context.bot.send_message(chat_id=chat_id, text=message_text)

                    follow_up_question = "Upr diye gye Question ka Answer kya hoga?👆"
                    await context.bot.send_poll(
                        chat_id=chat_id,
                        question=follow_up_question,
                        options=['A', 'B', 'C', 'D'],
                        type='quiz',
                        correct_option_id=correct_option_id,
                        explanation=description,
                        is_anonymous=True
                    )

                await asyncio.sleep(1)  # Minor delay between each poll
            except Exception as e:
                await context.bot.send_message(chat_id=chat_id, text="⚠️ CSV me kuch gadbadi hai.")
                continue


        countdown = 30
        msg = await context.bot.send_message(chat_id=chat_id, text=f"✅ Batch {batch_num+1} complete.\n⏳ Deleting in {countdown} seconds...")

        for i in range(countdown - 1, 0, -1):
            await asyncio.sleep(1)
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=msg.message_id,
                    text=f"✅ Batch {batch_num+1} complete.\n⏳ Deleting in {i} seconds..."
                )
            except:
                break  # agar user ne message delete kar diya ya edit fail hua to loop chhodo

# 30 second ke baad message delete
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
        except:
            pass
 # Wait before next batch

async def send_all_poll(chat_id, context: ContextTypes.DEFAULT_TYPE, questions):
    answer_mapping = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    max_question_length = 255
    max_option_length = 100
    max_description_length = 200

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

            # Check for missing data
            missing_data = False
            missing_elements = []

            if not text:
                missing_elements.append("Question")
                missing_data = True

            for index, option in enumerate(options):
                if not option:
                    missing_elements.append(f"Option {chr(65 + index)}")
                    missing_data = True

            if correct_option_id is None:
                missing_elements.append("Answer")
                missing_data = True

            if missing_data:
                # Notify about missing data
                message_text = (
                    f"Question: {text if text else '[Missing]'}\n\n"
                    f"Option A: {options[0] if options[0] else '[Missing]'}\n"
                    f"Option B: {options[1] if options[1] else '[Missing]'}\n"
                    f"Option C: {options[2] if options[2] else '[Missing]'}\n"
                    f"Option D: {options[3] if options[3] else '[Missing]'}\n"
                    f"Answer: {correct_option if correct_option else '[Missing]'}\n\n"
                    "Aapne jo MCQ bheja hai usme option ya Answer missing hai. Kripya use sudhar kr punh bheje."
                )
                await context.bot.send_message(chat_id=chat_id, text=message_text)
                continue

            # Ensure description contains "@SecondCoaching" and truncate if necessary
            if '@SecondCoaching' not in description:
                description = f"{description} @SecondCoaching" if description else "@SecondCoaching"

            if len(description) > max_description_length:
                description = description[:max_description_length].rsplit(' ', 1)[0] + "..."  # Truncate cleanly

            if len(text) <= max_question_length and all(len(option) <= max_option_length for option in options):
                # Send the poll if question and options fit Telegram limits
                await context.bot.send_poll(
                    chat_id=chat_id,
                    question=text,
                    options=options,
                    type='quiz',  # Use 'quiz' for quiz-type polls
                    correct_option_id=correct_option_id,
                    explanation=description,
                    is_anonymous=True  # Set to True to make the quiz anonymous
                )
            else:
                # Send the text-based question first
                message_text = (
                    f"🆀🆄🅴🆂🆃🅸🅾🅽: {text}\n\n"
                    f"🅾🅿🆃🅸🅾🅽 A: {options[0]}\n"
                    f"🅾🅿🆃🅸🅾🅽 B: {options[1]}\n"
                    f"🅾🅿🆃🅸🅾🅽 C: {options[2]}\n"
                    f"🅾🅿🆃🅸🅾🅽 D: {options[3]}\n"
                )
                await context.bot.send_message(chat_id=chat_id, text=message_text)

                # Follow up with a poll
                follow_up_question = "Upr diye gye Question ka Answer kya hoga?👆"
                follow_up_options = ['A', 'B', 'C', 'D']

                await context.bot.send_poll(
                    chat_id=chat_id,
                    question=follow_up_question,
                    options=follow_up_options,
                    type='quiz',
                    correct_option_id=correct_option_id,
                    explanation=description,
                    is_anonymous=True
                )
        except Exception as e:
            # Handle and notify about errors
            error_message = (
                "Aapne jo CSV file upload ki hai usme kuch gadbadi hai. "
                "Kripya use shi karke punh upload kre."
            )
            await context.bot.send_message(chat_id=chat_id, text=error_message)
            continue
                        
