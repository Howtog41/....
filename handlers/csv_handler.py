import csv
from telegram import Update
from telegram.ext import ContextTypes
from helpers.db import users_collection

UPLOAD_CSV, CHOOSE_DESTINATION = range(2)

async def upload_csv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if users_collection.find_one({'user_id': user_id}):
        await update.message.reply_text("Upload your CSV file.")
        return UPLOAD_CSV

async def handle_csv_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    file_path = f"{file.file_id}.csv"
    await file.download_to_drive(file_path)
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        questions = list(reader)
    
    context.user_data['questions'] = questions
    await update.message.reply_text("File received. Choose where to send quizzes.")
    return CHOOSE_DESTINATION
