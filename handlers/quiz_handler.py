import os
import csv
import re
from datetime import datetime
from telegram import Update, Poll, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)
from helpers.db import users_collection
from config import ADMIN_ID

# Global Data
quiz_data = []
file_title = "Quiz"
user_state = {}  # Stores each user's state: collecting, title, format

# -------------------- /GETCSV --------------------
async def getcsv(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        keyboard = [
            [InlineKeyboardButton("Telegram Format", callback_data="format_telegram")],
            [InlineKeyboardButton("Website Format", callback_data="format_website")]
        ]
        await update.message.reply_text(
            "📦 Choose the output CSV format:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        user_state[user_id] = {'collecting': False, 'title': False, 'format': None}
    else:
        await update.message.reply_text(
            "🚫 You are not authorized to use this command.\nYour trial may have expired.\nContact admin @lkd_ak"
        )

# -------------------- Format Selection --------------------
async def select_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in user_state:
        user_state[user_id] = {}

    if query.data == "format_telegram":
        user_state[user_id]['format'] = 'telegram'
        await query.edit_message_text("✅ Format selected: Telegram\n\nNow send me anonymous quiz polls.\nWhen done, type /done.")
    elif query.data == "format_website":
        user_state[user_id]['format'] = 'website'
        await query.edit_message_text("✅ Format selected: Website\n\nNow send me anonymous quiz polls.\nWhen done, type /done.")

    user_state[user_id]['collecting'] = True

# -------------------- ADD QUIZ --------------------
async def add_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global quiz_data
    user_id = update.effective_user.id

    if not user_state.get(user_id, {}).get('collecting', False):
        return

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

    if user_id not in user_state:
        await update.message.reply_text("⚠️ No active session found. Use /getcsv first.")
        return

    if user_state[user_id].get('title', False):
        title = update.message.text.strip()
        if not title:
            await update.message.reply_text("❗Title cannot be empty. Try again or type /skip.")
            return

        file_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        user_state[user_id]['title'] = False
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

# -------------------- GENERATE FILES --------------------
async def generate_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global quiz_data, file_title
    user_id = update.effective_user.id
    format_type = user_state.get(user_id, {}).get("format", "telegram")

    if not quiz_data:
        await update.message.reply_text("⚠️ No quiz data found. Please send some quizzes first.")
        return

    filename = f"{file_title}.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if format_type == "telegram":
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

        elif format_type == "website":
            for q in quiz_data:
                opts = q["options"]
                correct_index = opts.index(q["answer"]) if q["answer"] in opts else None
                correct_num = str(correct_index + 1) if correct_index is not None else ""

                row = [file_title, q["question"]] + opts
                while len(row) < 14:
                    row.append("")
                row.append(correct_num)

                writer.writerow(row)

    with open(filename, "rb") as f:
        await update.message.reply_document(f)

    os.remove(filename)
    quiz_data = []
    await update.message.reply_text("✅ File sent and data cleared.")

# -------------------- SETUP HANDLERS --------------------
def setup_handlers(app):
    app.add_handler(CommandHandler("getcsv", getcsv))
    app.add_handler(CallbackQueryHandler(select_format, pattern="^format_"))
    app.add_handler(CommandHandler("done", ask_title))
    app.add_handler(CommandHandler("skip", skip))
    app.add_handler(MessageHandler(filters.POLL, add_quiz))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_title))

