import re
import time

from telebot import TeleBot
from telebot import types
from datetime import datetime

from bot.bot import StatusBot, ErrorHandle
from prometheus.prometheus import Prometheus

BOT_NAME = 'Firi'
CHAT_ID = 'default_chat_id'
TOKEN = 'bot_api_token'

PROM = 'https://prometheus_server'
AUTH = ()

bot = TeleBot(TOKEN)
prom = Prometheus(PROM, AUTH)
status_bot = StatusBot(
    resource=prom,
    soul=bot
)


@bot.message_handler(commands=['update'])
def update_data(message):
    status_bot.status = None
    prom.clear_data()

    try:
        msg, error = prom.get_all_alias()
    except Exception:
        print(str(Exception))
        msg = "Update failed!"
        bot.reply_to(message, msg)

    if error == 0:
        msg = "Update successfuly!"
        status_bot.last_update_data = datetime.now().timestamp()
    else:
        msg += '\nPlease try later...'

    if message.text == '/update':
        bot.reply_to(message, msg)


@bot.message_handler(commands=['status'])
def get_status(message):
    status_bot.status = '/status'
    msg = 'Enter Job\'s name or Alias:'
    bot.reply_to(message, msg)
    this_time = datetime.now().timestamp()
    if this_time - status_bot.last_update_data > 600:
        update_data(message)
        status_bot.status = '/status'


@bot.message_handler(commands=['test'])
def test(message):
    msg = 'hello'

    bot.send_message(
        chat_id=message.chat.id,
        text=msg
    )


@bot.callback_query_handler(func=lambda message: True)
def answer(message):

    chat_id = message.message.chat.id

    raw = message.data
    msg = ''

    match = re.findall(r'\(([^)]+)\)(.*)', raw)
    data_type = match[0][0]
    data = match[0][1]
    if data_type == 'job':
        msg = status_bot.get_status(data)
    else:
        msg = prom.get_overview(data)

    bot.send_message(chat_id, msg)


@bot.message_handler(
    content_types=[
        'audio', 
        'document', 
        'photo', 
        'sticker', 
        'video', 
        'video_note', 
        'voice', 
        'location', 
        'contact', 
        'new_chat_members', 
        'left_chat_member', 
        'new_chat_title', 
        'new_chat_photo', 
        'delete_chat_photo', 
        'group_chat_created', 
        'supergroup_chat_created', 
        'channel_chat_created', 
        'migrate_to_chat_id', 
        'migrate_from_chat_id', 
        'pinned_message'
    ]
)
def why_handle(message):
    msg_type = str(message.content_type)
    msg = "Not support " + msg_type + '!'
    bot.reply_to(message, msg)


@bot.message_handler(regexp="^(sao|why).*")
def why_handle(message):
    if status_bot.status:
        return
    msg = "Đoán xem :D"
    bot.reply_to(message, msg)


@bot.message_handler(regexp="^[^/](.*)")
def text_handle(message):
    msg = ''

    if status_bot.status is None:
        msg = 'Please use command!'

    if status_bot.status == '/status':
        raw = message.json
        status_handle(
            chat_id=message.chat.id,
            key=raw.get('text')
        )
        return
    bot.reply_to(message, msg)


def status_handle(chat_id, key):
    result, sugg = status_bot.get_status(key)

    msg = result

    if msg:
        bot.send_message(
                chat_id=chat_id,
                text=msg
        )

    if sugg:
        msg = 'You may be try again with... '
        bot.send_message(
                chat_id=chat_id,
                text=msg
        )
    else:
        return

    if sugg['jobs']:
        msg = 'Job\'s name:'

        msg_jobs = get_keyboard_list(
            data=sugg['jobs'],
            tyle='job'
        )

        keyboard = make_keyboard(msg_jobs)
        bot.send_message(
            chat_id=chat_id,
            text=msg,
            reply_markup=keyboard
        )
    if sugg['aliases']:
        msg = 'Alias:'

        count = 0
        msg_aliases = get_keyboard_list(
            data=sugg['aliases'],
            tyle='alias'
        )

        keyboard = make_keyboard(msg_aliases)
        bot.send_message(
            chat_id=chat_id,
            text=msg,
            reply_markup=keyboard,
            parse_mode='HTML'
        )


def get_keyboard_list(data, tyle):
    keboard_list = []
    count = 0
    for item in data:
        score = item['score']
        if (score > 75) or \
           (score > 50 and count < 10) or \
           (score > 25 and count < 3) or \
           (score > 0 and count < 1):
            count += 1
            keboard_list.append(
                {
                    'text': item['key'] + ' (' + str(item['score']) + '%)',
                    'callback_data': item['key'],
                    'tyle': tyle
                }
            )
        else:
            break
    return keboard_list


def make_keyboard(list_item):

    keyboard = types.InlineKeyboardMarkup(row_width=20)
    for item in list_item:
        btn = types.InlineKeyboardButton(
            text=item['text'],
            callback_data='('+item['tyle']+')'+item['callback_data']
        )
        keyboard.add(btn)
    return keyboard


if __name__ == '__main__':

    while True:
        try:
            print('Bot restart at ', str(datetime.now()))
            bot.polling(True)
        except Exception:
            print('Something wrong...')
        print('Bot is sleeping...')
        bot.stop_polling()
        time.sleep(60)
