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
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    return response.json()['access_token']


def get_products(token):
    products_url = 'https://api.moltin.com/pcm/products'
    headers = {
        'Authorization': 'Bearer {}'.format(token),
    }
    response = requests.get(products_url, headers=headers)
    return response.json()


def get_product_by_id(product_id, token):
    # token = get_token(client_id, client_secret)
    headers = {
        'Authorization': f'Bearer {token}',
    }

    response = requests.get(f"https://api.moltin.com/pcm/catalog/products/{product_id}",
                            headers=headers)
    response.raise_for_status()

    return response.json()['data']


def get_product_stock(product, token):
    stock_url = f'https://api.moltin.com/v2/inventories/{product["id"]}'
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(stock_url, headers=headers)
    response.raise_for_status()
    return response.json()['data']['total']


def get_product_image(token, image_id):
    headers = {
        'Authorization': f'Bearer {token}',
    }
    response = requests.get(f'https://api.moltin.com/v2/files/{image_id}', headers=headers)
    response.raise_for_status()
    return response.json()


def create_cart(token):
    carts_url = 'https://api.moltin.com/v2/carts'
    headers = {
        'Authorization': 'Bearer {}'.format(token),
        'Content-Type': 'application/json',
    }
    data = {
        'data': {
            "name": "test",
        }
    }
    response = requests.post(carts_url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['data']['id']


def add_product_to_cart(cart_id, token, product, product_quantity):
    cart_url = f'https://api.moltin.com/v2/carts/{cart_id}/items/'
    headers = {
        'Authorization': 'Bearer {}'.format(token),
        'Content-Type': 'application/json',
    }
    data = {
        'data': {
            'id': product,
            'type': 'cart_item',
            'quantity': product_quantity,
        }
    }
    response = requests.post(cart_url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_cart(token, reference):
    cart_url = f'https://api.moltin.com/v2/carts/{reference}/items'
    headers = {
        'Authorization': 'Bearer {}'.format(token),
    }
    response = requests.get(cart_url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


if __name__ == '__main__':
    load_dotenv()
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']

    token = get_token(client_id, client_secret)

    products = get_products(token)
    product = products['data'][0]

    cart_id = create_cart(token)

    add_product_to_cart(cart_id, token, product)

    cart = get_cart(token, cart_id)
    print(222, cart)




