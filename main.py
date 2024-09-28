from telegram.ext import Application, CommandHandler, ConversationHandler, CallbackQueryHandler
from handlers.start_handler import start
from handlers.csv_handler import upload_csv_command, handle_csv_file
from handlers.poll_handler import choose_destination, channel_callback, send_all_polls
from handlers.channel_handler import set_channel, channels, channel_management_callback
from handlers.authorization_handler import authorize
from config import TOKEN
import logging
# Define states
# Define states
UPLOAD_CSV = 0  # Add this state for CSV upload handling
CHOOSE_DESTINATION = 1
CHOOSE_CHANNEL = 2

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Set to DEBUG to see more detailed logs
)
def main():
    application = Application.builder().token(TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("uploadcsv", upload_csv_command)],
        states={
            # Define stages for CSV upload and poll sending
            CHOOSE_DESTINATION: [
                CallbackQueryHandler(choose_destination, pattern="bot|channel")
            ],
            CHOOSE_CHANNEL: [
                CallbackQueryHandler(channel_callback)
            ]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    application.add_handler(conversation_handler)
    application.add_handler(CommandHandler("start", start))  # /start command
    application.add_handler(CommandHandler("setchannel", set_channel))
    application.add_handler(CommandHandler("channels", channels))
    application.add_handler(CommandHandler("authorize", authorize))
    application.add_handler(CallbackQueryHandler(channel_management_callback))

    application.run_polling()

if __name__ == "__main__":
    print("Bot is running...")
    main()
