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


def create_products_in_cart_buttons(products):
    keyboard = [
        [InlineKeyboardButton(f"Убрать из корзины {product['name']}",
                              callback_data=product['name'])]
        for product in products]
    keyboard.append(
        [InlineKeyboardButton('В меню', callback_data='menu'),
         InlineKeyboardButton('Оплатить', callback_data='email')]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def start(bot, update, token):
    reply_markup = create_products_buttons(token)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(bot, update, token):
    query = update.callback_query
    if query.data == 'cart':
        chat_id = update.callback_query.message.chat_id
        products_in_cart = get_cart(token)
    else:
        product_id = update.callback_query.data
        product = get_product_by_id(product_id, token)

        product_name = product['attributes']['name']
        product_description = product['attributes']['description']
        image_id = product['relationships']['main_image']['data']['id']
        image_url = get_product_image(token, image_id)['data']['link']['href']

        message = f"{product_name}\n\n{product_description}"
        bot.send_photo(chat_id=query.message.chat_id, photo=image_url, caption=message)
        return "START"


def get_database_connection():
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
    global _database
    if _database is None:
        database_password = os.getenv("DATABASE_PASSWORD")
        database_host = os.getenv("DATABASE_HOST")
        database_port = os.getenv("DATABASE_PORT")
        _database = redis.Redis(host=database_host, port=database_port, password=database_password)
    return _database


def handle_users_reply(update, context):
    db = context.bot_data['db']
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")
    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
    }
    state_handler = states_functions[user_state]
    next_state = state_handler(update, context)
    db.set(chat_id, next_state)


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
