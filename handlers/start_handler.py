from telegram import Update
from telegram.ext import ContextTypes
from helpers.db import users_collection

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_info = users_collection.find_one({'user_id': user_id})

    if user_info:
        await update.message.reply_text(
            "Welcome back! ʜɪ ᴛʜᴇʀᴇ!  \n"

            "➻ɪ'ᴍ ʏᴏᴜʀ ᴍᴄQ ʙᴏᴛ. 🤖 \n"

            "➻ᴜᴘʟᴏᴀᴅ ʏᴏᴜʀ ᴄꜱᴠ 📄ꜰɪʟᴇ ᴡɪᴛʜ ᴛʜᴇ ꜰᴏʟʟᴏᴡɪɴɢ ᴄᴏʟᴜᴍɴꜱ: \n"

            "👉Qᴜᴇꜱᴛɪᴏɴ, ᴏᴘᴛɪᴏɴ ᴀ, ᴏᴘᴛɪᴏɴ ʙ, ᴏᴘᴛɪᴏɴ ᴄ, ᴏᴘᴛɪᴏɴ ᴅ, ᴀɴꜱᴡᴇʀ, ᴅᴇꜱᴄʀɪᴘᴛɪᴏɴ.\n"

            "Use Command: -🔰 /uploadcsv."

            "➻ ɪ'ʟʟ ᴄᴏɴᴠᴇʀᴛ ɪᴛ ɪɴᴛᴏ ᴍᴜʟᴛɪᴘʟᴇ-ᴄʜᴏɪᴄᴇ Qᴜᴇꜱᴛɪᴏɴꜱ ꜰᴏʀ ʏᴏᴜ! \n"

            "• Mᴀɪɴᴛᴀɪɴᴇʀ: @How_to_Google \n"
        )
    else:
        users_collection.insert_one({'user_id': user_id})
        await update.message.reply_text(
            "Welcome ! ʜɪ ᴛʜᴇʀᴇ!  \n"

            "➻ɪ'ᴍ ʏᴏᴜʀ ᴍᴄQ ʙᴏᴛ. 🤖 \n"

            "➻ᴜᴘʟᴏᴀᴅ ʏᴏᴜʀ ᴄꜱᴠ 📄ꜰɪʟᴇ ᴡɪᴛʜ ᴛʜᴇ ꜰᴏʟʟᴏᴡɪɴɢ ᴄᴏʟᴜᴍɴꜱ: \n"

            "👉Qᴜᴇꜱᴛɪᴏɴ, ᴏᴘᴛɪᴏɴ ᴀ, ᴏᴘᴛɪᴏɴ ʙ, ᴏᴘᴛɪᴏɴ ᴄ, ᴏᴘᴛɪᴏɴ ᴅ, ᴀɴꜱᴡᴇʀ, ᴅᴇꜱᴄʀɪᴘᴛɪᴏɴ.\n"

            "Use Command: -🔰 /uploadcsv."

            "➻ ɪ'ʟʟ ᴄᴏɴᴠᴇʀᴛ ɪᴛ ɪɴᴛᴏ ᴍᴜʟᴛɪᴘʟᴇ-ᴄʜᴏɪᴄᴇ Qᴜᴇꜱᴛɪᴏɴꜱ ꜰᴏʀ ʏᴏᴜ! \n"

            "• Mᴀɪɴᴛᴀɪɴᴇʀ: @How_to_Google \n"
        )
