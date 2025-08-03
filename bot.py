from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
from handlers.set_description import get_set_description_handler

BOT_TOKEN = "7938208817:AAFWHdFfc8_NCyJrP_MhYpAZ7L3_9RHwgnA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot started. Use /setchanneldescription.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(get_set_description_handler())
    app.run_polling()

if __name__ == "__main__":
    main()
