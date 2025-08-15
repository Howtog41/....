import logging
import asyncio
from telegram.ext import Application, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.start_handler import start, help_menu
from handlers.csv_handler import upload_csv_command, handle_csv_file
from handlers.poll_handler import choose_destination, channel_callback, send_all_polls
from handlers.channel_handler import set_channel, channels, channel_management_callback
from handlers.authorization_handler import authorize
from handlers.channel_change_handler import change_channel, set_channel_name, receive_message, done
from handlers.quiz_handler import getcsv, add_quiz, ask_title, set_title, skip, select_format
from handlers.myplan import myplan
from config import TOKEN
from handlers.set_description import get_set_description_handler
from handlers.broadcast import setup_broadcast_handlers
from db import users_collection  # MongoDB users list

# Define states for the conversation
UPLOAD_CSV, CHOOSE_DESTINATION, CHOOSE_CHANNEL = range(3)
CHANNEL, MESSAGE = range(2)  # States for the change_channel conversation


# 🟢 Restart notifier
async def notify_restart(application):
    text = "♻ Bot has been restarted. Please continue your work."
    users = list(users_collection.find())

    for user in users:
        chat_id = user.get("chat_id")
        if not chat_id:
            continue
        try:
            await application.bot.send_message(chat_id=chat_id, text=text)
            await asyncio.sleep(0.05)  # Flood wait avoid
        except Exception as e:
            logging.warning(f"❌ Failed to send restart message to {chat_id}: {e}")


async def on_startup(app):
    await notify_restart(app)


def main():
    application = Application.builder().token(TOKEN).post_init(on_startup).build()

    # CSV conversation handler
    csv_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("uploadcsv", upload_csv_command)],
        states={
            UPLOAD_CSV: [MessageHandler(filters.Document.FileExtension("csv"), handle_csv_file)],
            CHOOSE_DESTINATION: [CallbackQueryHandler(choose_destination, pattern="bot|channel")],
            CHOOSE_CHANNEL: [CallbackQueryHandler(channel_callback)]
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    # Channel change conversation handler
    channel_change_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("change_channel", change_channel)],
        states={
            CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_channel)],
            MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, receive_message)]
        },
        fallbacks=[CommandHandler("done", done)],
        allow_reentry=True
    )

    # Handlers
    application.add_handler(csv_conversation_handler)
    application.add_handler(channel_change_conversation_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setchannel", set_channel))
    application.add_handler(CommandHandler("channels", channels))
    application.add_handler(CommandHandler("authorize", authorize))
    application.add_handler(get_set_description_handler())
    application.add_handler(CommandHandler("getcsv", getcsv))
    application.add_handler(CallbackQueryHandler(select_format, pattern="^format_"))
    application.add_handler(MessageHandler(filters.POLL, add_quiz))
    application.add_handler(CommandHandler("done", ask_title))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_title))
    application.add_handler(CommandHandler("skip", skip))
    application.add_handler(CommandHandler("myplan", myplan))
    application.add_handler(CallbackQueryHandler(channel_management_callback, pattern="^manage_.*"))
    application.add_handler(CallbackQueryHandler(help_menu, pattern="^help_menu$"))

    # Start bot
    application.run_polling()


if __name__ == "__main__":
    print("Bot is running...")
    main()
