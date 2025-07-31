from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from helpers.db import users_collection
from config import ADMIN_ID

# ✅ Authorize user command
async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        try:
            new_user_id = int(context.args[0])
            users_collection.update_one(
                {'user_id': new_user_id},
                {'$set': {'authorized': True}},
                upsert=True
            )
            await update.message.reply_text(f"User {new_user_id} has been authorized.")
        except IndexError:
            await update.message.reply_text("Usage: /authorize <user_id>")
        except ValueError:
            await update.message.reply_text("Invalid user ID. Please provide a numeric user ID.")
        except Exception as e:
            await update.message.reply_text(f"An error occurred: {str(e)}")
    else:
        await update.message.reply_text("You are not authorized to use this command.")

# ✅ List all authorized users
async def list_authorized(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    users = list(users_collection.find({'authorized': True}))
    if not users:
        await update.message.reply_text("No authorized users found.")
        return

    keyboard = []
    for user in users:
        uid = user['user_id']
        keyboard.append([
            InlineKeyboardButton(f"Remove {uid}", callback_data=f"remove_{uid}")
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Authorized Users:", reply_markup=reply_markup)

# ✅ Callback handler for removing authorized user
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("You are not authorized to perform this action.")
        return

    if query.data.startswith("remove_"):
        uid_to_remove = int(query.data.split("_")[1])
        users_collection.update_one(
            {'user_id': uid_to_remove},
            {'$set': {'authorized': False}}
        )
        await query.edit_message_text(f"User {uid_to_remove} has been removed from authorized list.")

# ✅ Handlers to be added in your main app
def register_handlers(application):
    application.add_handler(CommandHandler("authorize", authorize))
    application.add_handler(CommandHandler("listauthorized", list_authorized))
    application.add_handler(CallbackQueryHandler(button_handler))
