from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
from helpers.db import users_collection
from datetime import datetime, timedelta
import logging

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug("Received /start command")
    user_id = update.effective_user.id
    user_info = users_collection.find_one({'user_id': user_id})
    now = datetime.now()

    # Inline buttons
    keyboard = [
        [InlineKeyboardButton("🎥 Watch Tutorial", url="https://youtu.be/YOUR_VIDEO_LINK")],
        [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/lkd_ak")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if user_info:
        expires_on = user_info.get('expires_on')
        if expires_on and expires_on < now:
            await update.message.reply_text("⚠️ Your free trial has expired.\nContact admin for full access.", reply_markup=reply_markup)
        else:
            await update.message.reply_text(
                "Welcome back! ʜɪ ᴛʜᴇʀᴇ!  \n"
                "➻ɪ'ᴍ ʏᴏᴜʀ ᴍᴄQ ʙᴏᴛ. 🤖 \n"
                "➻ᴜᴘʟᴏᴀᴅ ʏᴏᴜʀ ᴄꜱᴠ 📄ꜰɪʟᴇ...\n"
                "Use Command: -🔰 /uploadcsv.\n"
                "• Mᴀɪɴᴛᴀɪɴᴇʀ: @How_to_Google \n",
                reply_markup=reply_markup
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
            "• Mᴀɪɴᴛᴀɪɴᴇʀ: @How_to_Google \n",
            reply_markup=reply_markup
            )

async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "**🤖 Bot Commands Menu:**\n\n"
        "/start - 🤖 Bot ko shuru karein aur welcome message dekhein\n"
        "/myplan - 📅 Aapka plan status aur bache hue din dekhein\n"
        "/uploadcsv - 📂 CSV upload karein MCQ banane ke liye\n"
        "/getcsv - 📤 CSV se quiz polls bhejne ke liye\n"
        "/done - ✅ Poll bhejna complete karein\n"
        "/setchannel - 📢 Channel set karein jahan content bhejna hai\n"
        "/channels - 📋 Set kiye gaye channels dekhein\n"
        "/authorize - 🔐 Kisi user ko access den (Admin only)\n"
        "/listauthorized - 📜 Authorized users ki list dekhein/hataayein (Admin only)\n"
        "/setchanneldescription - 📌 Channel tag ko MCQ me jodhne ke liye\n"
                                   )
