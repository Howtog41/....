from telegram import Update
from telegram.ext import ContextTypes
from helpers.db import users_collection

async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"Command called by user: {user_id}")

    if user_id == ADMIN_ID:
        print("Admin check passed")
        try:
            new_user_id = int(context.args[0])
            print(f"Authorizing user: {new_user_id}")

            users_collection.update_one(
                {'user_id': new_user_id},
                {'$set': {'authorized': True}},
                upsert=True
            )

            await update.message.reply_text(f"User {new_user_id} has been authorized.")
        except IndexError:
            print("Missing argument")
            await update.message.reply_text("Usage: /authorize <user_id>")
        except ValueError:
            print("Invalid argument")
            await update.message.reply_text("Invalid user ID. Please provide a numeric user ID.")
        except Exception as e:
            print(f"Unexpected error: {e}")
            await update.message.reply_text(f"An error occurred: {str(e)}")
    else:
        print("Admin check failed")
        await update.message.reply_text("You are not authorized to use this command.")
