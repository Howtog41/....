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

def chunk_questions(questions, chunk_size=19):
    for i in range(0, len(questions), chunk_size):
        yield questions[i:i + chunk_size]

async def send_all_polls(chat_id, context: ContextTypes.DEFAULT_TYPE, questions):
    answer_mapping = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    max_question_length = 255
    max_option_length = 100
    max_description_length = 200

    batches = list(chunk_questions(questions, chunk_size=19))

    for batch_index, batch in enumerate(batches):
        for question in batch:
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

                if not text or any(not opt for opt in options) or correct_option_id is None:
                    await context.bot.send_message(chat_id=chat_id, text="❌ Question ya options incomplete hai.")
                    continue

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
                    msg_text = (
                        f"🆀 {text}\n\n"
                        f"A: {options[0]}\nB: {options[1]}\nC: {options[2]}\nD: {options[3]}"
                    )
                    await context.bot.send_message(chat_id=chat_id, text=msg_text)

                    await context.bot.send_poll(
                        chat_id=chat_id,
                        question="Upr diye gye Question ka Answer kya hoga?👆",
                        options=["A", "B", "C", "D"],
                        type='quiz',
                        correct_option_id=correct_option_id,
                        explanation=description,
                        is_anonymous=True
                    )
                await asyncio.sleep(1)  # slight delay between questions

            except Exception as e:
                await context.bot.send_message(chat_id=chat_id, text="⚠️ Error in sending a question.")
                continue

        # Delay between batches to avoid flood limit
        if batch_index < len(batches) - 1:
            await context.bot.send_message(chat_id=chat_id, text="⏳ Next 19 questions loading...")
            await asyncio.sleep(5)  # longer delay between batches
                
