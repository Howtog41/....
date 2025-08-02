# 
# handlers/set_description.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# States
SET_CHOOSE, WAIT_DESCRIPTION = range(2)

# Step 1: Command: /setchanneldescription
async def set_channel_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = context.bot_data.get('channel_description')

    buttons = [[
        InlineKeyboardButton("✏️ Edit Description", callback_data='edit_description'),
        InlineKeyboardButton("❌ Delete Description", callback_data='delete_description')
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)

    if description:
        await update.message.reply_text(
            f"📌 Current Description:\n\n`{description}`",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "📝 Koi description set nahi hai.\nNaya description bhejne ke liye ✏️ Edit dabayein.",
            reply_markup=reply_markup
        )
    
    return SET_CHOOSE

# Step 2: Button click - edit or delete
async def description_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == 'edit_description':
        await query.edit_message_text("📝 Naya description bhejein (max 200 characters):")
        return WAIT_DESCRIPTION

    elif choice == 'delete_description':
        context.bot_data['channel_description'] = None
        await query.edit_message_text("🗑️ Description deleted successfully.")
        return ConversationHandler.END

# Step 3: Receive new description
async def receive_new_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_desc = update.message.text.strip()[:200]
    context.bot_data['channel_description'] = new_desc
    await update.message.reply_text(f"✅ Description saved:\n\n`{new_desc}`", parse_mode='Markdown')
    return ConversationHandler.END

# Step 4: Register Conversation Handler
def get_set_description_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("setchanneldescription", set_channel_description)],
        states={
            SET_CHOOSE: [CallbackQueryHandler(description_choice_callback)],
            WAIT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_description)],
        },
        fallbacks=[],
        )
