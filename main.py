import os

import requests as requests
from dotenv import load_dotenv


def get_token(client_id, client_secret):
    token_url = 'https://api.moltin.com/oauth/access_token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.get(token_url, data=data)
    response.raise_for_status()
    return response.json()['access_token']


def get_products(token):
    products_url = 'https://api.moltin.com/pcm/products'
    headers = {
        'Authorization': 'Bearer {}'.format(token),
    }
    response = requests.get(products_url, headers=headers)
    print(response.raise_for_status())
    return response.json()


def create_cart(token):
    carts_url = 'https://api.moltin.com/v2/carts'
    headers = {
        'Authorization': 'Bearer {}'.format(token),
        'Content-Type': 'application/json',
    }
    data = {
        'data': {
            "name": "Bob’s cart",
        }
    }
    response = requests.post(carts_url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['id']


if __name__ == '__main__':
    load_dotenv()
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']
    token = get_token(client_id, client_secret)
    products = get_products(token)
    product = products['data'][0]
    cart_id = create_cart(token)
    # cart = add_product_to_cart(client_id, token, product)
    print(create_cart(token))





