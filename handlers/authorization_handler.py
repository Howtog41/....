from telegram import Update
from telegram.ext import ContextTypes
from helpers.db import users_collection

async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        # Authorize a new user...
