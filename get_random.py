#!/usr/bin/env python2

from random import random, choice
from imgurpython import ImgurClient
import sys

client = None


def get_client(key, secret):
    global client
    if not client:
        client = ImgurClient(key, secret)
    return client


def get_random_image(client, gallery):
    gallery = client.subreddit_gallery(gallery, sort='new', window='all', page=int(random() * 100))
    item = choice(gallery)
    return item.link


if __name__ == '__main__':
    client = get_client('3e2eaf8ae012919', 'ec390933e8a8a0a3bccb171b3bec635bf12ba900')
    image = get_random_image(client, sys.argv[1])
    print image
