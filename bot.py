import functools

from dotenv import load_dotenv
import os

import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

from elasticpath import get_token, get_products, get_product_by_id, get_cart, get_product_image, get_product_stock, add_product_to_cart

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
    if update.callback_query:
        bot.send_message(chat_id=update.callback_query.message['chat']['id'], text='Please choose:', reply_markup=reply_markup)
    elif update.message:
        update.message.reply_text('Please choose:', reply_markup=reply_markup)
    bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    return "HANDLE_MENU"


def handle_menu(bot, update, token):
    query = update.callback_query
    if query.data == 'cart':
        chat_id = update.callback_query.message.chat_id
        products_in_cart = get_cart(token)
    product_id = update.callback_query.data
    product = get_product_by_id(product_id, token)

    product_name = product['attributes']['name']
    product_price = product['meta']['display_price']['with_tax']['formatted']
    product_description = product['attributes']['description']
    product_stock = get_product_stock(product, token)

    image_id = product['relationships']['main_image']['data']['id']
    image_url = get_product_image(token, image_id)['data']['link']['href']

    message = f"{product_name}\n\n{product_price} per kg\n{product_stock} kg on stock\n\n{product_description}"
    keyboard = [[InlineKeyboardButton('1 кг', callback_data=f'{query.data},1'),
                 InlineKeyboardButton('5 кг', callback_data=f'{query.data},5'),
                 InlineKeyboardButton('10 кг', callback_data=f'{query.data},10')],
                [InlineKeyboardButton('Назад', callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard, n_cols=3)
    bot.send_photo(chat_id=query.message.chat_id, photo=image_url, caption=message, reply_markup=reply_markup)
    # bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    return 'HANDLE_DESCRIPTION'


def handle_description(bot, update, token):
    query = update.callback_query
    chat_id = update.callback_query.message.chat_id

    print('handle_description_data', query.data)
    if query.data == 'back':
        start(bot, update, token)
        return "HANDLE_MENU"
    else:
        product_id, product_quantity = query.data.split(',')
        add_product_to_cart(chat_id, token, product_id, int(product_quantity))
        cart = get_cart(token, chat_id)
        return "HANDLE_DESCRIPTION"


def get_database_connection(host, port, password):
    """
    Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан.
    """
    global _database
    if _database is None:
        _database = redis.Redis(host=host, port=port, password=password)
    return _database


def handle_users_reply(bot, update, host, port, password, client_id, client_secret):
    db = get_database_connection(host, port, password)
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
    token = get_token(client_id, client_secret)
    states_functions = {
        'START': functools.partial(start, token=token),
        'HANDLE_MENU': functools.partial(handle_menu, token=token),
        'HANDLE_DESCRIPTION': functools.partial(handle_description, token=token)
    }
    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']

    elasticpath_token = get_token(client_id, client_secret)

    db_host = os.environ['DATABASE_HOST']
    db_port = os.environ['DATABASE_PORT']
    db_password = os.environ['DATABASE_PASSWORD']

    partial_handle_users_reply = functools.partial(handle_users_reply, host=db_host, port=db_port, password=db_password, client_id=client_id, client_secret=client_secret)

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(partial_handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, partial_handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', partial_handle_users_reply))

    updater.start_polling()
