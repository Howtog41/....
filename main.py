from telegram.ext import Application, CommandHandler, ConversationHandler
from handlers.start_handler import start
from handlers.csv_handler import upload_csv_command, handle_csv_file
from handlers.poll_handler import choose_destination, channel_callback, send_all_polls
from handlers.channel_handler import set_channel, channels, channel_management_callback
from handlers.authorization_handler import authorize
from config import TOKEN

def main():
    application = Application.builder().token(TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("uploadcsv", upload_csv_command)],
        states={
            # Define stages for CSV upload and poll sending
        },
        fallbacks=[CommandHandler("start", start)]
    )

    application.add_handler(conversation_handler)
    application.add_handler(CommandHandler("setchannel", set_channel))
    application.add_handler(CommandHandler("channels", channels))
    application.add_handler(CommandHandler("authorize", authorize))

    application.run_polling()

if __name__ == "__main__":
    main()
