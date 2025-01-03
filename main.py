import logging
from telegram.ext import Application, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.start_handler import start
from handlers.csv_handler import upload_csv_command, handle_csv_file
from handlers.poll_handler import choose_destination, channel_callback, send_all_polls
from handlers.channel_handler import set_channel, channels, channel_management_callback
from handlers.authorization_handler import authorize
from handlers.channel_change_handler import change_channel, set_channel, receive_message, done  # Import the new handler functions
from config import TOKEN

# Define states for the conversation
UPLOAD_CSV, CHOOSE_DESTINATION, CHOOSE_CHANNEL = range(3)
CHANNEL, MESSAGE = range(2)  # States for the change_channel conversation

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Set to DEBUG to see more detailed logs
)

def main():
    application = Application.builder().token(TOKEN).build()

    # Define the CSV conversation handler
    csv_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("uploadcsv", upload_csv_command)],  # Entry point for the CSV upload command
        states={
            UPLOAD_CSV: [MessageHandler(filters.Document.FileExtension("csv"), handle_csv_file)],  # CSV file handler
            CHOOSE_DESTINATION: [CallbackQueryHandler(choose_destination, pattern="bot|channel")],  # Choose bot or channel
            CHOOSE_CHANNEL: [CallbackQueryHandler(channel_callback)]  # Channel selection callback
        },
        fallbacks=[CommandHandler("start", start)], # Fallback to start command
        allow_reentry=True
    )

    # Define the channel change conversation handler
    channel_change_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("change_channel", change_channel)],  # Start with /change_channel
        states={
            CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_channel)],  # Set the new channel name
            MESSAGE: [MessageHandler(filters.ALL & ~filters.COMMAND, receive_message)]  # Receive messages
        },
        fallbacks=[CommandHandler("done", done)],  # End the conversation with /done
        allow_reentry=True
    )

    # Add handlers to the application
    application.add_handler(csv_conversation_handler)  # CSV upload handler
    application.add_handler(channel_change_conversation_handler)  # Change channel handler
    application.add_handler(CommandHandler("start", start))  # /start command
    application.add_handler(CommandHandler("setchannel", set_channel))  # /setchannel command
    application.add_handler(CommandHandler("channels", channels))  # /channels command
    application.add_handler(CommandHandler("authorize", authorize))  # /authorize command
    application.add_handler(CallbackQueryHandler(channel_management_callback))  # Channel management callback

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    print("Bot is running...")
    main()
