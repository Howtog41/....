from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from helpers.db import users_collection

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

async def send_all_polls(chat_id, context: ContextTypes.DEFAULT_TYPE, questions):
    answer_mapping = {'1': 0, '2': 1, '3': 2, '4': 3}
    max_question_length = 255
    max_option_length = 100
    max_description_length = 200

    for question in questions:
        try:
            text = question.get('Question')
            options = [
                question.get('Option A', ''), 
                question.get('Option B', ''), 
                question.get('Option C', ''), 
                question.get('Option D', '')
            ]
            correct_option = question.get('Answer')
            correct_option_id = answer_mapping.get(correct_option.upper(), None) if correct_option else None
            description = question.get('Description', '')

            # Check for missing data
            missing_data = False
            missing_elements = []

            if not text:
                missing_elements.append("Question")
                missing_data = True

            for index, option in enumerate(options):
                if option == '':
                    missing_elements.append(f"Option {chr(65 + index)}")
                    missing_data = True

            if correct_option is None:
                missing_elements.append("Answer")
                missing_data = True

            if missing_data:
                # Prepare a message showing the MCQ and indicating the missing data
                message_text = f"Question: {text if text else '[Missing]'}\n\n"
                message_text += f"Option A: {options[0] if options[0] else '[Missing]'}\n"
                message_text += f"Option B: {options[1] if options[1] else '[Missing]'}\n"
                message_text += f"Option C: {options[2] if options[2] else '[Missing]'}\n"
                message_text += f"Option D: {options[3] if options[3] else '[Missing]'}\n"
                message_text += f"Answer: {correct_option if correct_option else '[Missing]'}\n"
                message_text += "\nAapne jo MCQ bheja hai usme option ya Answer missing hai. Kripya use sudhar kr punh bheje."
                
                await context.bot.send_message(chat_id=chat_id, text=message_text)
                continue

            # Ensure description contains "@SecondCoaching"
            if '@SecondCoaching' not in description:
                if description:
                    description += ' @SecondCoaching'
                else:
                    description = '@SecondCoaching'

            if (len(text) <= max_question_length and 
                all(len(option) <= max_option_length for option in options) and 
                len(description) <= max_description_length):

                # Send the poll
                await context.bot.send_poll(
                    chat_id=chat_id,
                    question=text,
                    options=options,
                    type='quiz',  # Use 'quiz' for quiz-type polls
                    correct_option_id=correct_option_id,
                    explanation=description,
                    is_anonymous=True  # Set to True to make the quiz anonymous
                )
                await asyncio.sleep(1) 
            else:
                # Send the question and options as a text message
                message_text = f"Question: {text}\n\n"
                message_text += f"Option A: {options[0]}\n"
                message_text += f"Option B: {options[1]}\n"
                message_text += f"Option C: {options[2]}\n"
                message_text += f"Option D: {options[3]}\n"
                if description:
                    message_text += f"\nDescription: {description}"

                await context.bot.send_message(chat_id=chat_id, text=message_text)

                # Send a follow-up quiz
                follow_up_question = "Upr diye gye Question ka Answer kya hoga?👆👆👆👆👆👆👆👆👆"
                follow_up_options = ['A', 'B', 'C', 'D']

                await context.bot.send_poll(
                    chat_id=chat_id,
                    question=follow_up_question,
                    options=follow_up_options,
                    type='quiz',
                    correct_option_id=correct_option_id,
                    is_anonymous=True
                )
        except Exception as e:
            error_message = "Aapne jo CSV file upload ki hai usme kuch gadbadi hai. Kripya use shi karke punh upload kre."
            await context.bot.send_message(chat_id=chat_id, text=error_message)
            continue
