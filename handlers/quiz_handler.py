import os
import csv
import re
from telegram import Update, Poll
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from helpers.db import users_collection
from config import ADMIN_ID

# Global Data
quiz_data = []
file_title = "Quiz"
user_state = {}  # Stores each user's state (collecting/title)

# -------------------- GETCSV --------------------
async def getcsv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_info = users_collection.find_one({'user_id': user_id})

    if user_id == ADMIN_ID or (user_info and user_info.get('authorized', False)):
        user_state[user_id] = {'collecting': True, 'title': False}
        await update.message.reply_text(
            "✅ Authorized.\n\nSend me anonymous quiz polls (quiz mode only).\nWhen finished, type /done."
        )
    else:
        await update.message.reply_text(
            "🚫 You are not authorized to use this command.\nContact admin @lkd_ak"
        )

# -------------------- ADD QUIZ --------------------
async def add_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global quiz_data
    user_id = update.effective_user.id

    # Check if quiz collection is active
    if not user_state.get(user_id, {}).get('collecting', False):
        return  # Ignore if not in quiz collection mode

    if update.message.poll and update.message.poll.type == Poll.QUIZ:
        poll = update.message.poll
        question = re.sub(r"^\[.*?\]\s*", "", poll.question)
        options = [opt.text for opt in poll.options]
        correct_option_id = poll.correct_option_id

        explanation = poll.explanation if poll.explanation else ""
        explanation = re.sub(r"@\w+", "", explanation)
        explanation = re.sub(r"https?://\S+|www\.\S+", "", explanation)
        explanation = explanation.strip()

        correct_answer = options[correct_option_id] if correct_option_id is not None else "No correct answer"

        quiz_data.append({
            "question": question,
            "options": options,
            "answer": correct_answer,
            "description": explanation
        })

        await update.message.reply_text(
            f"✅ Added: '{question[:50]}...'\nSend more or type /done."
        )
    else:
        await update.message.reply_text("⚠️ Please send an *anonymous quiz poll* (in quiz mode).")

# -------------------- /DONE COMMAND --------------------
async def ask_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not user_state.get(user_id, {}).get('collecting', False):
        await update.message.reply_text("❗Start with /getcsv first.")
        return

    user_state[user_id]['collecting'] = False
    user_state[user_id]['title'] = True

    await update.message.reply_text(
        "📄 Please send a title for the CSV file.\nOr type /skip to use the default title 'Quiz'."
    )

# -------------------- SET TITLE --------------------

async def set_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global file_title
    user_id = update.effective_user.id

    # Debug check
    if user_id not in user_state:
        await update.message.reply_text("⚠️ No active session found. Use /getcsv first.")
        return

    if user_state[user_id].get('title', False):
        title = update.message.text.strip()

        if not title:
            await update.message.reply_text("❗Title cannot be empty. Try again or type /skip.")
            return

        # Sanitize filename
        file_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        user_state[user_id]['title'] = False  # reset
        await update.message.reply_text(f"✅ Title set to: {file_title}\nGenerating file...")
        await generate_files(update, context)
    else:
        await update.message.reply_text("⚠️ Not expecting a title now. Use /getcsv to start.")

# -------------------- /SKIP COMMAND --------------------
async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_state.get(user_id, {}).get('title', False):
        user_state[user_id]['title'] = False
        await update.message.reply_text("📂 Using default title 'Quiz'. Generating file...")
        await generate_files(update, context)

# -------------------- GENERATE CSV FILE --------------------
async def generate_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global quiz_data, file_title

    if not quiz_data:
        await update.message.reply_text("⚠️ No quiz data found. Please send some quizzes first.")
        return

    filename = f"{file_title}.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Question", "Option A", "Option B", "Option C", "Option D", "Answer", "Description"])
        for q in quiz_data:
            opts = q["options"]
            correct_index = opts.index(q["answer"]) if q["answer"] in opts else None
            correct_letter = chr(65 + correct_index) if correct_index is not None else "N/A"

            writer.writerow([
                q["question"],
                opts[0] if len(opts) > 0 else "",
                opts[1] if len(opts) > 1 else "",
                opts[2] if len(opts) > 2 else "",
                opts[3] if len(opts) > 3 else "",
                correct_letter,
                q["description"]
            ])

    # Send CSV to user
    with open(filename, "rb") as f:
        await update.message.reply_document(f)

    os.remove(filename)
    quiz_data = []
    await update.message.reply_text("✅ File sent and data cleared.")

# -------------------- SETUP HANDLERS (in main.py or entry point) --------------------

def setup_handlers(app):
    app.add_handler(CommandHandler("getcsv", getcsv))
    app.add_handler(CommandHandler("done", ask_title))
    app.add_handler(CommandHandler("skip", skip))
    app.add_handler(MessageHandler(filters.POLL, add_quiz))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_title))
