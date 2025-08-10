from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from helpers.db import users_collection
from config import ADMIN_ID

# -------------------- /BROADCAST COMMAND --------------------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 Only admin can use this command.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Usage: /broadcast <message>")
        return

    message_text = " ".join(context.args)

    # Get all authorized users
    users = users_collection.find({"authorized": True})
    sent_count = 0

    for user in users:
        try:
            await context.bot.send_message(chat_id=user["user_id"], text=message_text)
            sent_count += 1
        except Exception as e:
            print(f"Failed to send to {user['user_id']}: {e}")

    await update.message.reply_text(f"✅ Broadcast sent to {sent_count} users.")

# -------------------- HANDLER SETUP --------------------
def setup_broadcast_handlers(app):
    app.add_handler(CommandHandler("broadcast", broadcast))
