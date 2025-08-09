import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

logger = logging.getLogger(__name__)

SET_CHOOSE, WAIT_DESCRIPTION = range(2)

# --- CONFIG: choose storage mode ---
# "user"  -> each Telegram user has their own description (private)
# "chat"  -> each chat/group has its own description (shared in that chat)
# "global"-> bot_data keeps a mapping chat_id -> description (also per-chat,
#            useful if you want explicit per-channel map)
STORAGE_MODE = "user"   # change to "chat" or "global" as needed
DEFAULT_DESCRIPTION = "@How_To_Google"
MAX_LEN = 200

# --- helper functions to get/set/delete description depending on STORAGE_MODE ---
def _get_desc_key_for_global(update: Update):
    return update.effective_chat.id

def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if STORAGE_MODE == "user":
        return context.user_data.get("channel_description")
    elif STORAGE_MODE == "chat":
        return context.chat_data.get("channel_description")
    else:  # global mapping by chat_id
        chat_id = _get_desc_key_for_global(update)
        descriptions = context.bot_data.setdefault("channel_descriptions", {})
        return descriptions.get(chat_id)

def set_description(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    if STORAGE_MODE == "user":
        context.user_data["channel_description"] = text
    elif STORAGE_MODE == "chat":
        context.chat_data["channel_description"] = text
    else:
        chat_id = _get_desc_key_for_global(update)
        descriptions = context.bot_data.setdefault("channel_descriptions", {})
        descriptions[chat_id] = text

def reset_to_default(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # either remove custom key or set default — here we set default explicitly
    if STORAGE_MODE == "user":
        context.user_data["channel_description"] = DEFAULT_DESCRIPTION
    elif STORAGE_MODE == "chat":
        context.chat_data["channel_description"] = DEFAULT_DESCRIPTION
    else:
        chat_id = _get_desc_key_for_global(update)
        descriptions = context.bot_data.setdefault("channel_descriptions", {})
        descriptions[chat_id] = DEFAULT_DESCRIPTION

# --- Conversation handlers ---
async def set_channel_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ensure a default exists for this user/chat if none set yet
    desc = get_description(update, context)
    if desc is None:
        # set explicit default so UI shows default and delete behaves consistently
        set_description(update, context, DEFAULT_DESCRIPTION)
        desc = DEFAULT_DESCRIPTION

    # build buttons: show Delete only if current value != DEFAULT_DESCRIPTION
    buttons = [InlineKeyboardButton("✏️ Edit Description", callback_data="edit_description")]
    if desc != DEFAULT_DESCRIPTION:
        buttons.append(InlineKeyboardButton("❌ Delete Description", callback_data="delete_description"))

    reply_markup = InlineKeyboardMarkup([buttons])

    await update.message.reply_text(
        f"📌 Current Description:\n\n`{desc}`",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return SET_CHOOSE

async def description_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data
    logger.info(f"Button clicked: {choice}")

    if choice == "edit_description":
        # prompt user to send new description
        # we edit the same message so UI looks clean
        await query.edit_message_text("📝 Send new description (max 200 characters). Send /cancel to abort.")
        return WAIT_DESCRIPTION

    elif choice == "delete_description":
        # reset to default (not global deletion)
        reset_to_default(update, context)
        await query.edit_message_text(f"🗑️ Description reset to default:\n\n`{DEFAULT_DESCRIPTION}`", parse_mode="Markdown")
        return ConversationHandler.END

async def receive_new_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if len(text) == 0:
        await update.message.reply_text("⚠️ Empty description — please send some text or /cancel.")
        return WAIT_DESCRIPTION
    if len(text) > MAX_LEN:
        await update.message.reply_text(f"⚠️ Description {MAX_LEN} characters se zyada nahi ho sakti. Abhi {len(text)} characters hain. Kripya chhota karke bhejein.")
        return WAIT_DESCRIPTION

    set_description(update, context, text)
    await update.message.reply_text(
        f"✅ New description set:\n\n`{text}`",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # works for both callback-query (if user typed /cancel) and normal message
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("❌ Operation cancelled.")
    else:
        await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

def get_set_description_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("setchanneldescription", set_channel_description)],
        states={
            SET_CHOOSE: [
                CallbackQueryHandler(description_choice_callback, pattern="^(edit_description|delete_description)$")
            ],
            WAIT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_description)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True,
        allow_reentry=True
    )

