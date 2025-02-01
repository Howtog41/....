import os
import csv
import re
import time
from telegram import Update, Poll
from telegram.ext import ContextTypes

# Global variables
user_states = {}  # Track states per user
user_quiz_data = {}  # Store quiz data for each user


async def getcsv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the bot and set the state."""
    user_id = update.effective_user.id
    user_states[user_id] = "COLLECTING_QUIZ"
    user_quiz_data[user_id] = []

    await update.message.reply_text(
        "Welcome! Send me anonymous quizzes in quiz mode, and I'll save them as a CSV file. "
        "When you're done, type 'done' to generate the file."
    )


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages based on their state."""
    user_id = update.effective_user.id
    state = user_states.get(user_id)
    message = update.message.text

    if not state:
        await update.message.reply_text("Please start by typing /start.")
        return

    if state == "COLLECTING_QUIZ":
        if update.message.poll:
            # Add the quiz data
            await add_quiz(update, context)
        elif message.lower() == "done":
            user_states[user_id] = "SETTING_TITLE"
            await ask_title(update, context)
        else:
            await update.message.reply_text(
                "Please send me a quiz (in quiz mode) or type 'done' to finish."
            )
    elif state == "SETTING_TITLE":
        if message.lower() == "skip":
            await skip_title(update, context)
        else:
            await set_title(update, context)


async def add_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a quiz to the user's data."""
    user_id = update.effective_user.id
    user_data = user_quiz_data[user_id]

    poll = update.message.poll
    if poll.type != Poll.QUIZ:
        await update.message.reply_text("Please send an anonymous quiz in quiz mode.")
        return

    question = re.sub(r"^\[.*?\]\s*", "", poll.question)  # Clean question
    options = [opt.text for opt in poll.options]
    correct_option_id = poll.correct_option_id
    correct_answer = options[correct_option_id] if correct_option_id is not None else "No correct answer provided"
    explanation = poll.explanation or ""
    explanation = re.sub(r"@\w+|https?://\S+|www\.\S+", "", explanation).strip()

    user_data.append({
        "question": question,
        "options": options,
        "answer": correct_answer,
        "description": explanation,
    })
    await update.message.reply_text(
        f"Question added: '{question}'\nSend more or type 'done' to finish."
    )


async def ask_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask the user for a title for the CSV file."""
    await update.message.reply_text(
        "Please provide a title for the CSV file or type 'skip' to use a default title."
    )


async def set_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the title and generate the CSV file."""
    user_id = update.effective_user.id
    file_title = re.sub(r"[^\w\s-]", "", update.message.text).strip() or "Quiz"
    file_title += f"_{int(time.time())}"  # Append timestamp
    await generate_files(update, context, file_title)


async def skip_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip setting the title and use the default."""
    file_title = f"Quiz_{int(time.time())}"  # Default title with timestamp
    await generate_files(update, context, file_title)


async def generate_files(update: Update, context: ContextTypes.DEFAULT_TYPE, file_title: str):
    """Generate a CSV file from the user's quiz data."""
    user_id = update.effective_user.id
    user_data = user_quiz_data[user_id]

    if not user_data:
        await update.message.reply_text("No quiz data found. Please send some quizzes first.")
        return

    csv_file_path = f"{file_title}.csv"
    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Question", "Option A", "Option B", "Option C", "Option D", "Answer", "Description"])
        for quiz in user_data:
            options = quiz["options"]
            csv_writer.writerow([
                quiz["question"],
                options[0] if len(options) > 0 else "",
                options[1] if len(options) > 1 else "",
                options[2] if len(options) > 2 else "",
                options[3] if len(options) > 3 else "",
                quiz["answer"],
                quiz["description"]
            ])

    with open(csv_file_path, "rb") as csv_file:
        await update.message.reply_document(csv_file)

    os.remove(csv_file_path)  # Clean up the file
    user_states[user_id] = None  # Reset state
    user_quiz_data[user_id] = []  # Clear data

    await update.message.reply_text("Your quiz file has been generated and sent!")


# Entry points for handlers
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log and notify errors."""
    await update.message.reply_text("An error occurred. Please try again.")
