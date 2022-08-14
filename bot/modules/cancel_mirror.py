from telegram import InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
from time import sleep
from threading import Thread

from bot import download_dict, dispatcher, download_dict_lock, SUDO_USERS, OWNER_ID, AUTO_DELETE_MESSAGE_DURATION
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage, sendMarkup, auto_delete_message
from bot.helper.ext_utils.bot_utils import getDownloadByGid, MirrorStatus, getAllDownload
from bot.helper.telegram_helper import button_build


def cancel_mirror(update, context):
    args = update.message.text.split(" ", maxsplit=1)
    user_id = update.message.from_user.id
    if len(context.args) == 1:
        gid = context.args[0]
        dl = getDownloadByGid(gid)
        if not dl:
            return sendMessage(f"GID: <code>{gid}</code> 𝐍𝐨𝐭 𝐅𝐨𝐮𝐧𝐝.", context.bot, update.message)
    elif update.message.reply_to_message:
        mirror_message = update.message.reply_to_message
        with download_dict_lock:
            if mirror_message.message_id in download_dict:
                dl = download_dict[mirror_message.message_id]
            else:
                dl = None
        if not dl:
            return sendMessage("𝐓𝐡𝐢𝐬 𝐢𝐬 𝐧𝐨𝐭 𝐚𝐧 𝐚𝐜𝐭𝐢𝐯𝐞 𝐭𝐚𝐬𝐤!", context.bot, update.message)
    elif len(context.args) == 0:
        msg = f"𝐑𝐞𝐩𝐥𝐲 𝐭𝐨 𝐚𝐧 𝐚𝐜𝐭𝐢𝐯𝐞 <code>/{BotCommands.MirrorCommand}</code> 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐰𝐡𝐢𝐜𝐡 \
                𝐰𝐚𝐬 𝐮𝐬𝐞𝐝 𝐭𝐨 𝐬𝐭𝐚𝐫𝐭 𝐭𝐡𝐞 𝐝𝐨𝐰𝐧𝐥𝐨𝐚𝐝 𝐨𝐫 𝐬𝐞𝐧𝐝 <code>/{BotCommands.CancelMirror} GID</code> 𝐭𝐨 𝐜𝐚𝐧𝐜𝐞𝐥 𝐢𝐭!"
        return sendMessage(msg, context.bot, update.message)

    if OWNER_ID != user_id and dl.message.from_user.id != user_id and user_id not in SUDO_USERS:
        return sendMessage("This task is not for you!", context.bot, update.message)

    dl.download().cancel_download()

def cancel_all(status):
    gid = ''
    while True:
        dl = getAllDownload(status)
        if dl:
            if dl.gid() != gid:
                gid = dl.gid()
                dl.download().cancel_download()
                sleep(1)
        else:
            break

def cancell_all_buttons(update, context):
    buttons = button_build.ButtonMaker()
    buttons.sbutton("Downloading", "canall down")
    buttons.sbutton("Uploading", "canall up")
    buttons.sbutton("Seeding", "canall seed")
    buttons.sbutton("Cloning", "canall clone")
    buttons.sbutton("Extracting", "canall extract")
    buttons.sbutton("Archiving", "canall archive")
    buttons.sbutton("Splitting", "canall split")
    buttons.sbutton("All", "canall all")
    if AUTO_DELETE_MESSAGE_DURATION == -1:
        buttons.sbutton("Close", "canall close")
    button = InlineKeyboardMarkup(buttons.build_menu(2))
    can_msg = sendMarkup('Choose tasks to cancel.', context.bot, update.message, button)
    Thread(target=auto_delete_message, args=(context.bot, update.message, can_msg)).start()

def cancel_all_update(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    data = data.split()
    if CustomFilters._owner_query(user_id):
        query.answer()
        if data[1] == 'close':
            query.message.delete()
            return
        query.message.delete()
        cancel_all(data[1])
    else:
        query.answer(text="𝐘𝐨𝐮 𝐝𝐨𝐧'𝐭 𝐡𝐚𝐯𝐞 𝐩𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧 𝐭𝐨 𝐮𝐬𝐞 𝐭𝐡𝐞𝐬𝐞 𝐛𝐮𝐭𝐭𝐨𝐧𝐬!", show_alert=True)



cancel_mirror_handler = CommandHandler(BotCommands.CancelMirror, cancel_mirror,
                                       filters=(CustomFilters.authorized_chat | CustomFilters.authorized_user), run_async=True)

cancel_all_handler = CommandHandler(BotCommands.CancelAllCommand, cancell_all_buttons,
                                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)

cancel_all_buttons_handler = CallbackQueryHandler(cancel_all_update, pattern="canall", run_async=True)

dispatcher.add_handler(cancel_all_handler)
dispatcher.add_handler(cancel_mirror_handler)
dispatcher.add_handler(cancel_all_buttons_handler)