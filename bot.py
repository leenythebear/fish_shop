import functools

from dotenv import load_dotenv
import os

import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

from elasticpath import get_token, get_products

_database = None


def create_products_buttons(token):
    """
    Функция для создания кнопок меню с товарами
    """
    products = get_products(token)['data']
    print(products[0])
    keyboard = [
        [InlineKeyboardButton(product['attributes']['name'], callback_data=product['id'])]
        for product in products]
    keyboard.append(
        [InlineKeyboardButton('Корзина', callback_data='cart')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def start(bot, update, token):
    reply_markup = create_products_buttons(token)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(bot, update):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его написать "/start",
    поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может воспользоваться этой командой.
    """
    # db = get_database_connection()
    users_reply = update.callback_query
    if users_reply.data == 'cart':
        message = 'Вы перешли в корзину'
        bot.send_message(text=message,
                         chat_id=users_reply.message.chat_id)
    # if update.message:
    #     user_reply = update.message.text
    #     chat_id = update.message.chat_id
    # elif update.callback_query:
    #     user_reply = update.callback_query.data
    #     chat_id = update.callback_query.message.chat_id
    # else:
    #     return
    # if user_reply == '/start':
    #     user_state = 'START'
    # else:
    #     user_state = db.get(chat_id).decode("utf-8")
    #
    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
    }

    # state_handler = states_functions[user_state]
    # Если вы вдруг не заметите, что python-telegram-bot перехватывает ошибки.
    # Оставляю этот try...except, чтобы код не падал молча.
    # Этот фрагмент можно переписать.
    # try:
    #     next_state = state_handler(bot, update)
    #     db.set(chat_id, next_state)
    # except Exception as err:
    #     print(err)
#
#
# def get_database_connection():
#     """
#     Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан.
#     """
#     global _database
#     if _database is None:
#         database_password = os.getenv("DATABASE_PASSWORD")
#         database_host = os.getenv("DATABASE_HOST")
#         database_port = os.getenv("DATABASE_PORT")
#         _database = redis.Redis(host=database_host, port=database_port,
#                                 password=database_password)
#     return _database


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']

    elasticpath_token = get_token(client_id, client_secret)
    updater = Updater(token)
    dispatcher = updater.dispatcher
    # dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    # dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    # dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', functools.partial(start, token=elasticpath_token)))
    dispatcher.add_handler(CommandHandler(handle_menu))
    updater.start_polling()
