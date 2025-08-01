from telegram import Update
from telegram.ext import ContextTypes
from helpers.db import users_collection
from datetime import datetime, timedelta
import logging

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("Received /start command")
    user_id = update.effective_user.id
    user_info = users_collection.find_one({'user_id': user_id})
    now = datetime.now()

    if user_info:
        expires_on = user_info.get('expires_on')
        if expires_on and expires_on < now:
            await update.message.reply_text("⚠️ Your free trial has expired.\nContact admin for full access.")
        else:
            await update.message.reply_text(
                "Welcome back! ʜɪ ᴛʜᴇʀᴇ!  \n"
                "➻ɪ'ᴍ ʏᴏᴜʀ ᴍᴄQ ʙᴏᴛ. 🤖 \n"
                "➻ᴜᴘʟᴏᴀᴅ ʏᴏᴜʀ ᴄꜱᴠ 📄ꜰɪʟᴇ...\n"
                "Use Command: -🔰 /uploadcsv.\n"
                "• Mᴀɪɴᴛᴀɪɴᴇʀ: @How_to_Google \n"
            )
    else:
        users_collection.insert_one({
            'user_id': user_id,
            'authorized': True,
            'authorized_on': now,
            'expires_on': now + timedelta(days=3)
        })
        await update.message.reply_text(
            "🎉 ʜɪ ᴛʜᴇʀᴇ!  \n"
            "➻ You’ve been given *3 days free trial access.*\n"
            "➻ᴜᴘʟᴏᴀᴅ ʏᴏᴜʀ ᴄꜱᴠ 📄ꜰɪʟᴇ...\n"
            "Use Command: -🔰 /uploadcsv.\n"
            "• Mᴀɪɴᴛᴀɪɴᴇʀ: @How_to_Google \n"
        )
