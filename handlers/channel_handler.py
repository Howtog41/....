from telegram import Update
from telegram.ext import ContextTypes
from helpers.db import users_collection

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        # Code to add a channel to the user's list

async def channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # List the available channels for the admin
