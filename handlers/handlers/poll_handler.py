from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from helpers.db import users_collection

async def choose_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    # Handle bot or channel selection logic...

async def send_all_polls(chat_id, context: ContextTypes.DEFAULT_TYPE, questions):
    # Sends all the questions as polls...
