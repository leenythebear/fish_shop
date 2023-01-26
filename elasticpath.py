import os

import requests as requests
from dotenv import load_dotenv


def get_token(client_id, client_secret):
    token_url = "https://api.moltin.com/oauth/access_token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def get_products(token):
    products_url = "https://api.moltin.com/pcm/products"
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    response = requests.get(products_url, headers=headers)
    return response.json()


def get_product_by_id(product_id, token):
    # token = get_token(client_id, client_secret)
    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = requests.get(
        f"https://api.moltin.com/pcm/catalog/products/{product_id}",
        headers=headers,
    )
    response.raise_for_status()

    return response.json()["data"]


def get_product_stock(product, token):
    stock_url = f'https://api.moltin.com/v2/inventories/{product["id"]}'
    headers = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(stock_url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]["total"]


def get_product_image(token, image_id):
    headers = {
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(
        f"https://api.moltin.com/v2/files/{image_id}", headers=headers
    )
    response.raise_for_status()
    return response.json()


def create_cart(token):
    carts_url = "https://api.moltin.com/v2/carts"
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }
    data = {
        "data": {
            "name": "test",
        }
    }
    response = requests.post(carts_url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["data"]["id"]


def add_product_to_cart(cart_id, token, product, product_quantity):
    cart_url = f"https://api.moltin.com/v2/carts/{cart_id}/items/"
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }
    data = {
        "data": {
            "id": product,
            "type": "cart_item",
            "quantity": product_quantity,
        }
    }
    response = requests.post(cart_url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_cart(token, chat_id):
    cart_url = f"https://api.moltin.com/v2/carts/{chat_id}/items"
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    response = requests.get(cart_url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]


def delete_product_from_cart(token, product_id, chat_id):
    url = f"https://api.moltin.com/v2/carts/{chat_id}/items/{product_id}"
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def get_carts_sum(token, chat_id):
    carts_sum_url = f"https://api.moltin.com/v2/carts/{chat_id}"
    headers = {
        "Authorization": "Bearer {}".format(token),
    }
    response = requests.get(carts_sum_url, headers=headers)
    response.raise_for_status()
    return response.json()["data"]["meta"]["display_price"]["with_tax"][
        "formatted"
    ]


def create_customer(token, email, chat_id):
    url = f"https://api.moltin.com/v2/customers"
    headers = {
        "Authorization": "Bearer {}".format(token),
        "Content-Type": "application/json",
    }
    json_data = {
        "data": {
            "type": "customer",
            "name": str(chat_id),
            "email": email,
            "password": "",
        },
    }
    response = requests.post(url, headers=headers, json=json_data)
    response.raise_for_status()
