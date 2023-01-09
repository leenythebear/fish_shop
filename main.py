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


if __name__ == '__main__':
    load_dotenv()
    client_id = os.environ['CLIENT_ID']
    client_secret = os.environ['CLIENT_SECRET']
    # token = os.environ['TOKEN']
    token = get_token(client_id, client_secret)
    print(get_products(token))
    print(token)


