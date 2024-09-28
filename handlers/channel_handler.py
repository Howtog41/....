from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, InlineKeyboardButton, InlineKeyboardMarkup
from helpers.db import users_collection
from config import ADMIN_ID
async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id == ADMIN_ID:

        try:

            channel_id = context.args[0]

            users_collection.update_one({'user_id': user_id}, {'$addToSet': {'channels': channel_id}})

            await update.message.reply_text(f"Channel ID {channel_id} has been added.")

        except IndexError:

            await update.message.reply_text("Usage: /setchannel <channel_id>")

    else:

        await update.message.reply_text("You are not authorized to use this command.")

# Command to manage channels

async def channels(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id == ADMIN_ID:

        user_info = users_collection.find_one({'user_id': user_id})

        channels = user_info.get('channels', [])

        if not channels:

            await update.message.reply_text("No channels are set. Use /setchannel <channel_id> to add a new channel.")

            return

        

        keyboard = [

            [InlineKeyboardButton(channel, callback_data=f"remove_{channel}") for channel in channels],

            [InlineKeyboardButton("Add new channel", callback_data="add_channel")]

        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Manage your channels:", reply_markup=reply_markup)

    else:

        await update.message.reply_text("You are not authorized to use this command.")

# Handle channel management callbacks

async def channel_management_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    data = query.data

    if data == "add_channel":

        await query.edit_message_text(text="Please use /setchannel <channel_id> to add a new channel.")

    elif data.startswith("remove_"):

        channel_id = data.split("_", 1)[1]

        user_id = update.effective_user.id

        users_collection.update_one({'user_id': user_id}, {'$pull': {'channels': channel_id}})

        await query.edit_message_text(text=f"Channel {channel_id} has been removed.")
