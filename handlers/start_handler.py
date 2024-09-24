from telegram import Update
from telegram.ext import ContextTypes
from helpers.db import users_collection

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_info = users_collection.find_one({'user_id': user_id})

    if user_info:
        await update.message.reply_text(
            "Welcome back! Upload your CSV file using /uploadcsv."
        )
    else:
        users_collection.insert_one({'user_id': user_id})
        await update.message.reply_text(
            "Welcome! Upload your CSV file using /uploadcsv."
        )
