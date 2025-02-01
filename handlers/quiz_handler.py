import os
import csv
import re
from telegram import Update, Poll
from telegram.ext import ContextTypes

# Global variables
quiz_data = []
file_title = "Quiz"  # Default title
bot_state = None  # To track the bot's state


async def getcsv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the main flow of the bot."""
    global bot_state

    await update.message.reply_text(
        "Welcome! Send me an anonymous quiz, and I'll save it as a CSV file. "
        "When you're done, type 'done' to generate the file."
    )

    bot_state = "collecting_quiz"  # Set state for collecting quiz

    while True:
        # Wait for the user's response
        user_message = update.message.text  # Get the user's message directly

        if user_message and user_message[-1].message:
            message = user_message[-1].message.text

            if bot_state == "collecting_quiz" and user_message[-1].poll:
                await add_quiz(user_message[-1], context)
            elif bot_state == "collecting_quiz" and message.lower() == "done":
                await ask_title(update, context)
                break
            elif bot_state == "title":
                if message.lower() == "skip":
                    await skip(update, context)
                else:
                    await set_title(update, context)
                break


async def add_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add quiz data from anonymous polls."""
    global quiz_data
    if update.poll and update.poll.type == Poll.QUIZ:
        poll = update.poll
        question = poll.question

        # Remove any leading [ ] from the question
        question = re.sub(r"^\[.*?\]\s*", "", question)

        options = [opt.text for opt in poll.options]
        correct_option_id = poll.correct_option_id

        # Process the description to remove links, usernames, and URLs
        explanation = poll.explanation if poll.explanation else ""
        explanation = re.sub(r"@\w+", "", explanation)  # Remove @username
        explanation = re.sub(r"https?://\S+|www\.\S+", "", explanation)  # Remove links and URLs
        explanation = explanation.strip()  # Remove extra spaces

        # Ensure correct answer is identified
        correct_answer = options[correct_option_id] if correct_option_id is not None else "No correct answer provided"

        quiz_data.append({
            "question": question,
            "options": options,
            "answer": correct_answer,
            "description": explanation
        })
        await update.message.reply_text(
            f"Quiz question added: '{question}'\nSend more or type 'done' to save the file."
        )
    else:
        await update.message.reply_text("Please send an anonymous quiz (in quiz mode).")


async def ask_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for the title."""
    global bot_state
    bot_state = "title"
    await update.message.reply_text(
        "Please provide a title for the CSV file, or type 'skip' to use the default title."
    )


async def set_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set the file title."""
    global file_title, bot_state
    file_title = update.message.text
    bot_state = None  # Reset the state
    await generate_files(update, context)


async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip title setting."""
    global bot_state
    if bot_state == "title":
        bot_state = None
        await update.message.reply_text("Using default title. Generating the file...")
        await generate_files(update, context)


async def generate_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a CSV file from the collected quiz data."""
    global quiz_data, file_title

    if not quiz_data:
        await update.message.reply_text("No quiz data found. Please send some quizzes first.")
        return

    # Generate .csv file
    csv_file_path = f"{file_title}.csv"
    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        # Write header
        csv_writer.writerow(["Question", "Option A", "Option B", "Option C", "Option D", "Answer", "Description"])
        for quiz in quiz_data:
            options = quiz["options"]
            correct_index = quiz["options"].index(quiz["answer"]) if quiz["answer"] in quiz["options"] else None
            correct_option_letter = chr(65 + correct_index) if correct_index is not None else "N/A"  # Convert to A, B, C, D
            csv_writer.writerow([
                quiz["question"],
                options[0] if len(options) > 0 else "",
                options[1] if len(options) > 1 else "",
                options[2] if len(options) > 2 else "",
                options[3] if len(options) > 3 else "",
                correct_option_letter,
                quiz["description"]  # Add the cleaned description
            ])

    # Send the CSV file to the user
    with open(csv_file_path, "rb") as csv_file:
        await update.message.reply_document(csv_file)

    # Cleanup
    os.remove(csv_file_path)
    quiz_data = []  # Reset the quiz data
