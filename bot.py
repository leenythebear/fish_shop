import functools

from dotenv import load_dotenv
import os

import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

from elasticpath import get_token, get_products, get_product_by_id, get_cart, get_product_image

_database = None


def create_products_buttons(token):
    """
    Функция для создания кнопок меню с товарами
    """
    products = get_products(token)['data']
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
        keyboard = [[InlineKeyboardButton('Назад', callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        print(111, type(reply_markup))
        # print(111, dict(bot.send_photo))
        bot.send_photo(chat_id=query.message.chat_id, photo=image_url, caption=message, reply_markup=reply_markup)
        return 'HANDLE_DESCRIPTION'


def handle_description(bot, update, token):
    query = update.callback_query
    print(1234566778)
    if query.data == 'back':
        return "START"


def get_database_connection():
    """
    Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан.
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
    elif user_reply == 'back':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode("utf-8")
    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
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

    db_host = os.environ['DATABASE_HOST']
    db_port = os.environ['DATABASE_PORT']
    db_password = os.environ['DATABASE_PASSWORD']

    database = redis.Redis(host=db_host, port=db_port, password=db_password)

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', functools.partial(start, token=elasticpath_token)))
    dispatcher.add_handler(CallbackQueryHandler(functools.partial(handle_menu, token=elasticpath_token)))
    dispatcher.add_handler(CallbackQueryHandler(functools.partial(handle_users_reply, token=elasticpath_token)))

    updater.start_polling()
