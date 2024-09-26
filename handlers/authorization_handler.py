from telegram import Update
from telegram.ext import ContextTypes
from helpers.db import users_collection

async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id == ADMIN_ID:

        try:

            new_user_id = int(context.args[0])

            users_collection.update_one({'user_id': new_user_id}, {'$set': {'authorized': True}}, upsert=True)

            await update.message.reply_text(f"User {new_user_id} has been authorized.")

        except (IndexError, ValueError):

            await update.message.reply_text("Usage: /authorize <user_id>")

    else:

        await update.message.reply_text("You are not authorized to use this command.")
