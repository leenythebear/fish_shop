import functools
from textwrap import dedent

from dotenv import load_dotenv
import os

import redis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from validate_email import validate_email

from elasticpath import (
    get_token,
    get_products,
    get_product_by_id,
    get_cart,
    get_product_image,
    get_product_stock,
    add_product_to_cart,
    get_carts_sum,
    delete_product_from_cart,
    create_customer,
)

_database = None


def create_products_buttons(token):
    """
    Функция для создания кнопок меню с товарами
    """
    products = get_products(token)["data"]
    keyboard = [
        [
            InlineKeyboardButton(
                product["attributes"]["name"], callback_data=product["id"]
            )
        ]
        for product in products
    ]
    keyboard.append([InlineKeyboardButton("Корзина", callback_data="cart")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def start(bot, update, token):
    reply_markup = create_products_buttons(token)
    if update.callback_query:
        bot.send_message(
            chat_id=update.callback_query.message["chat"]["id"],
            text="Please choose:",
            reply_markup=reply_markup,
        )
    elif update.message:
        update.message.reply_text("Please choose:", reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(bot, update, token):
    query = update.callback_query
    if query.data == "cart":
        handle_cart(bot, update, token)
        return "HANDLE_CART"
    product_id = update.callback_query.data
    product = get_product_by_id(product_id, token)

    product_name = product["attributes"]["name"]
    product_price = product["meta"]["display_price"]["with_tax"]["formatted"]
    product_description = product["attributes"]["description"]
    product_stock = get_product_stock(product, token)

    image_id = product["relationships"]["main_image"]["data"]["id"]
    image_url = get_product_image(token, image_id)["data"]["link"]["href"]

    message = f"{product_name}\n\n{product_price} per kg\n{product_stock} kg on stock\n\n{product_description}"
    keyboard = [
        [
            InlineKeyboardButton("1 кг", callback_data=f"{query.data},1"),
            InlineKeyboardButton("5 кг", callback_data=f"{query.data},5"),
            InlineKeyboardButton("10 кг", callback_data=f"{query.data},10"),
        ],
        [InlineKeyboardButton("Назад", callback_data="start")],
        [InlineKeyboardButton("Корзина", callback_data="cart")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard, n_cols=3)
    bot.send_photo(
        chat_id=query.message.chat_id,
        photo=image_url,
        caption=message,
        reply_markup=reply_markup,
    )
    return "HANDLE_DESCRIPTION"


def handle_description(bot, update, token):
    query = update.callback_query
    chat_id = query["message"]["chat"]["id"]
    if query.data == "start":
        start(bot, update, token)
        return "HANDLE_MENU"
    elif query.data == "cart":
        handle_cart(bot, update, token)
        return "HANDLE_CART"
    else:
        split_query = query.data.split(",")
        if len(split_query) == 2:
            product_id, product_quantity = split_query
            add_product_to_cart(
                chat_id, token, product_id, int(product_quantity)
            )
            bot.answer_callback_query(
                callback_query_id=query.id,
                text="Товар добавлен в корзину",
                show_alert=False,
            )
        return "HANDLE_DESCRIPTION"


def handle_cart(bot, update, token):
    query = update.callback_query
    chat_id = query["message"]["chat"]["id"]
    if query.data == "cart":
        products_cart = get_cart(token, chat_id)
        carts_sum = get_carts_sum(token, chat_id)
        message = ""
        for product in products_cart:
            cart_description = f"""\
                                   {product["name"]}
                                   {product["description"]} 
                                   {product["unit_price"]["amount"]} per kg 
                                   {product["quantity"]} kg in cart for ${product["value"]["amount"]}
                                   ______________________________
                                    
                                    """
            message += dedent(cart_description)
        sum_message = f"""\
                            Total: {carts_sum}
                                
                        """
        message += dedent(sum_message)
        keyboard = [
            [
                InlineKeyboardButton(
                    f'Удалить {product["name"]}',
                    callback_data=f'delete,{product["id"]}',
                )
            ]
            for product in products_cart
        ]
        if products_cart:
            keyboard.append(
                [InlineKeyboardButton("Оплата", callback_data="pay")]
            )
        keyboard.append([InlineKeyboardButton("Меню", callback_data="start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(
            chat_id=chat_id, text=message, reply_markup=reply_markup
        )
        return "HANDLE_DESCRIPTION"
    elif query.data == "start":
        start(bot, update, token)
        return "HANDLE_MENU"
    elif query.data.startswith("delete"):
        product_id = query.data.split(",")[1]
        delete_product_from_cart(token, product_id, chat_id)
        bot.answer_callback_query(
            callback_query_id=query.id,
            text="Товар удален из корзины",
            show_alert=False,
        )
        products_cart = get_cart(token, chat_id)
        carts_sum = get_carts_sum(token, chat_id)
        message = ""
        for product in products_cart:
            cart_description = f"""\
                                    {product["name"]}
                                    {product["description"]} 
                                    {product["unit_price"]["amount"]} per kg 
                                    {product["quantity"]} kg in cart for ${product["value"]["amount"]}
                                    ______________________________

                                    """
            message += dedent(cart_description)
        sum_message = f"""\
                                    Total: {carts_sum}

                                """
        message += dedent(sum_message)
        keyboard = [
            [
                InlineKeyboardButton(
                    f'Удалить {product["name"]}',
                    callback_data=f'delete,{product["id"]}',
                )
            ]
            for product in products_cart
        ]
        if products_cart:
            keyboard.append(
                [InlineKeyboardButton("Оплата", callback_data="pay")]
            )
        keyboard.append([InlineKeyboardButton("Меню", callback_data="start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(
            chat_id=chat_id, text=message, reply_markup=reply_markup
        )
        return "HANDLE_DESCRIPTION"
    elif query.data == "pay":
        bot.send_message(chat_id=chat_id, text="Введите Ваш email:")
        return "WAITING_EMAIL"


def waiting_email(bot, update, token):
    email = update.message.text
    chat_id = update.message.chat_id
    is_valid = validate_email(email_address=email)
    if is_valid:
        create_customer(token, email, chat_id)
        bot.send_message(chat_id=chat_id, text="Ваш заказ создан")
        start(bot, update, token)
        return "START"
    else:
        bot.send_message(chat_id=chat_id, text="Введите корректный email")
        return "WAITING_EMAIL"


def get_database_connection(host, port, password):
    """
    Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан.
    """
    global _database
    if _database is None:
        _database = redis.Redis(host=host, port=port, password=password)
    return _database


def handle_users_reply(
    bot, update, host, port, password, client_id, client_secret
):
    db = get_database_connection(host, port, password)
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == "/start":
        user_state = "START"
    else:
        user_state = db.get(chat_id).decode("utf-8")
    token = get_token(client_id, client_secret, db)
    states_functions = {
        "START": functools.partial(start, token=token),
        "HANDLE_MENU": functools.partial(handle_menu, token=token),
        "HANDLE_DESCRIPTION": functools.partial(
            handle_description, token=token
        ),
        "HANDLE_CART": functools.partial(handle_cart, token=token),
        "WAITING_EMAIL": functools.partial(waiting_email, token=token),
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(bot, update)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    client_id = os.environ["CLIENT_ID"]
    client_secret = os.environ["CLIENT_SECRET"]

    db_host = os.environ["DATABASE_HOST"]
    db_port = os.environ["DATABASE_PORT"]
    db_password = os.environ["DATABASE_PASSWORD"]

    partial_handle_users_reply = functools.partial(
        handle_users_reply,
        host=db_host,
        port=db_port,
        password=db_password,
        client_id=client_id,
        client_secret=client_secret,
    )

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(partial_handle_users_reply))
    dispatcher.add_handler(
        MessageHandler(Filters.text, partial_handle_users_reply)
    )
    dispatcher.add_handler(CommandHandler("start", partial_handle_users_reply))

    updater.start_polling()
