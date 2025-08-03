# 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# States
SET_CHOOSE, WAIT_DESCRIPTION = range(2)

# Step 1: /setchanneldescription command
async def set_channel_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = context.bot_data.get('channel_description', None)

    keyboard = [[
        InlineKeyboardButton("✏️ Edit Description", callback_data="edit_description"),
        InlineKeyboardButton("❌ Delete Description", callback_data="delete_description")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if description:
        await update.message.reply_text(
            f"📌 Current Description:\n\n`{description}`",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "⚠️ No description set yet.\nClick ✏️ Edit to set one.",
            reply_markup=reply_markup
        )

    return SET_CHOOSE


# Step 2: CallbackQuery (Edit/Delete)
async def description_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "edit_description":
        await query.edit_message_text("📝 Send new description (max 200 characters):")
        return WAIT_DESCRIPTION

    elif choice == "delete_description":
        context.bot_data['channel_description'] = None
        await query.edit_message_text("🗑️ Description deleted.")
        return ConversationHandler.END


# Step 3: Receive new description
async def receive_new_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text.strip()[:200]
    context.bot_data['channel_description'] = description

    await update.message.reply_text(
        f"✅ New description set:\n\n`{description}`",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ✅ Return handler from function
def get_set_description_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("setchanneldescription", set_channel_description)],
        states={
            SET_CHOOSE: [CallbackQueryHandler(description_choice_callback)],
            WAIT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_description)],
        },
        fallbacks=[],
        )
