from telegram import Update
from telegram.ext import ContextTypes
from helpers.db import users_collection
from datetime import datetime

async def myplan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_info = users_collection.find_one({'user_id': user_id})
    now = datetime.now()

    if not user_info:
        await update.message.reply_text(
            "❌ You are not registered yet. Use /start to begin your free trial."
        )
        return

    start_date = user_info.get('authorized_on')
    end_date = user_info.get('expires_on')
    authorized = user_info.get('authorized', False)

    if not (start_date and end_date):
        await update.message.reply_text("⚠️ Plan details not found. Please contact admin @lkd_ak.")
        return

    remaining_days = (end_date - now).days
    status = "✅ Active" if end_date > now and authorized else "❌ Expired"

    text = (
        f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
        f"📅 <b>Plan Start:</b> <code>{start_date.strftime('%Y-%m-%d')}</code>\n"
        f"⏳ <b>Plan Expires:</b> <code>{end_date.strftime('%Y-%m-%d')}</code>\n"
        f"🕒 <b>Remaining Days:</b> <code>{max(0, remaining_days)} day(s)</code>\n"
        f"📌 <b>Status:</b> {status}\n\n"
        f"🤖 <b>Bot Info:</b>\n"
        f"- Upload CSV to convert into MCQs\n"
        f"- Get polls for quizzes and explanations\n"
        f"- Works with anonymous quiz polls\n\n"
        f"👮 <b>Admin Contact:</b> @lkd_ak"
    )

    await update.message.reply_text(text, parse_mode="HTML")
