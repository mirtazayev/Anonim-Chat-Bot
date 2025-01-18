import telebot
from telebot import types

from database import add_communications, recovery_data, free_users, add_users, communications, delete_info, \
    update_user_like, delete_user_from_db, session
from messages import m_is_connect, m_is_not_free_users, m_send_some_messages, dislike_str, like_str, m_play_again, \
    m_all_like, m_dislike_user_to, m_dislike_user, m_like, m_failed, m_good_bye, m_disconnect_user, m_start, \
    m_is_not_user_name, m_has_not_dialog
from models import User

access_token = '5664043616:AAEdrBd551QLBPOGFyU_Q0tx8kIh6xOQq3Q'
bot = telebot.TeleBot(access_token)


def inline_menu():
    callback = types.InlineKeyboardButton(text='\U00002709 Yangi suxbat', callback_data='NewChat')
    menu = types.InlineKeyboardMarkup()
    menu.add(callback)

    return menu


def generate_markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
    markup.add(like_str)
    markup.add(dislike_str)
    return markup


def connect_user(user_id):
    if user_id in communications:
        return True
    else:
        bot.send_message(user_id, m_has_not_dialog, reply_markup=inline_menu())
        return False


@bot.message_handler(commands=['start'])
def echo(message):
    message.chat.type = 'private'
    user_id = message.chat.id

    if message.chat.username is None:
        bot.send_message(user_id, m_is_not_user_name)
        return

    menu = inline_menu()

    bot.send_message(user_id, m_start, reply_markup=menu)


@bot.message_handler(commands=['stop'])
def echo(message):
    menu = types.ReplyKeyboardRemove()
    user_id = message.chat.id

    if message.chat.id in communications:
        bot.send_message(communications[user_id]['UserTo'], m_disconnect_user, reply_markup=menu)

        tmp_id = communications[user_id]['UserTo']
        delete_info(tmp_id)

    delete_user_from_db(user_id)

    bot.send_message(user_id, m_good_bye)


@bot.message_handler(func=lambda call: call.text == like_str or call.text == dislike_str)
def echo(message):
    user_id = message.chat.id

    if user_id not in communications:
        bot.send_message(user_id, m_failed, reply_markup=types.ReplyKeyboardRemove())
        return

    user_to_id = communications[user_id]['UserTo']

    flag = False

    if message.text == dislike_str:
        bot.send_message(user_id, m_dislike_user, reply_markup=types.ReplyKeyboardRemove())
        bot.send_message(user_to_id, m_dislike_user_to, reply_markup=types.ReplyKeyboardRemove())
        flag = True
    else:
        bot.send_message(user_id, m_like, reply_markup=types.ReplyKeyboardRemove())

        update_user_like(user_to_id)

        if communications[user_id]['like'] == communications[user_to_id]['like']:
            bot.send_message(user_id, m_all_like(communications[user_id]['UserName']))
            bot.send_message(user_to_id, m_all_like(communications[user_to_id]['UserName']))
            flag = True

    if flag:
        delete_info(user_to_id)
        menu = inline_menu()
        bot.send_message(user_id, m_play_again, reply_markup=menu)
        bot.send_message(user_to_id, m_play_again, reply_markup=menu)


@bot.message_handler(content_types=['text', 'sticker', 'video', 'photo', 'audio', 'voice'])
def echo(message):
    user_id = message.chat.id
    if message.content_type == 'sticker':
        if not connect_user(user_id):
            return

        bot.send_sticker(communications[user_id]['UserTo'], message.sticker.file_id)
    elif message.content_type == 'photo':
        if not connect_user(user_id):
            return

        file_id = None

        for item in message.photo:
            file_id = item.file_id

        bot.send_photo(communications[user_id]['UserTo'], file_id, caption=message.caption)
    elif message.content_type == 'audio':
        if not connect_user(user_id):
            return

        bot.send_audio(communications[user_id]['UserTo'], message.audio.file_id, caption=message.caption)
    elif message.content_type == 'video':
        if not connect_user(user_id):
            return

        bot.send_video(communications[user_id]['UserTo'], message.video.file_id, caption=message.caption)
    elif message.content_type == 'voice':
        if not connect_user(user_id):
            return

        bot.send_voice(communications[user_id]['UserTo'], message.voice.file_id)
    elif message.content_type == 'text':
        if message.text != '/start' and message.text != '/stop' and \
                message.text != dislike_str and message.text != like_str and message.text != 'NewChat':

            if not connect_user(user_id):
                return

            if message.reply_to_message is None:
                bot.send_message(communications[user_id]['UserTo'], message.text)
            elif message.from_user.id != message.reply_to_message.from_user.id:
                bot.send_message(communications[user_id]['UserTo'], message.text,
                                 reply_to_message_id=message.reply_to_message.message_id - 1)
            else:
                bot.send_message(user_id, m_send_some_messages)


@bot.callback_query_handler(func=lambda call: True)
def echo(call):
    if call.data == 'NewChat':
        user_id = call.message.chat.id
        user_to_id = None

        add_users(chat=call.message.chat)

        if len(free_users) < 2:
            bot.send_message(user_id, m_is_not_free_users)
            return

        if free_users[user_id]['state'] == 0:
            return

        for user in free_users:
            if user['state'] == 0:
                user_to_id = user['ID']
                break

        if user_to_id is None:
            bot.send_message(user_id, m_is_not_free_users)
            return

        keyboard = generate_markup()

        add_communications(user_id, user_to_id)

        bot.send_message(user_id, m_is_connect, reply_markup=keyboard)
        bot.send_message(user_to_id, m_is_connect, reply_markup=keyboard)


def get_all_users():
    """Retrieve all user IDs from the database using SQLAlchemy."""
    try:
        users = session.query(User.id).all()
        return [user[0] for user in users]
    finally:
        session.close()


@bot.message_handler(commands=['send'])
def send_mode(message):
    """Enable the /send command to forward messages."""
    bot.send_message(message.chat.id, "Please send the message you want to forward to all users.")

    @bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio'])
    def forward_to_all(inner_message):
        """Forward messages to all users."""
        if inner_message.chat.type == 'private':  # Ensure private chat
            user_id = inner_message.chat.id
            user_ids = get_all_users()
            for uid in user_ids:
                if uid != user_id:  # Skip sender
                    try:
                        if inner_message.content_type == 'text':
                            bot.send_message(uid, inner_message.text)
                        else:
                            bot.forward_message(uid, inner_message.chat.id, inner_message.message_id)
                    except Exception as e:
                        print(f"Could not forward to user {uid}: {e}")
            bot.send_message(user_id, "Your message has been forwarded to all users!")


if __name__ == '__main__':
    recovery_data()
    bot.stop_polling()
    bot.polling(none_stop=True)
