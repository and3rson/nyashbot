# coding: utf-8

from __future__ import print_function

import telegram
import mechanize
import re
from urllib import urlencode
from random import choice, random
from bs4 import BeautifulSoup
from db import DB
import json
from HTMLParser import HTMLParser


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def translate(src, dest, text):
    PATTERN = 'http://translate.google.com/translate_a/t?client=x&text={text}&hl={src}&sl={src}&tl={dest}'
    url = PATTERN.format(src=src, dest=dest, text=text.replace(' ', '+'))

    browser = mechanize.Browser()
    browser.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')]
    browser.set_handle_robots(False)
    browser.open('https://translate.google.com')
    browser.select_form(nr=0)

    browser.form['sl'] = [src]
    browser.form['tl'] = [dest]
    browser.form['text'] = text
    response = browser.submit()
    doc = BeautifulSoup(response.read())
    return ''.join([x.text for x in doc.select('span#result_box > span')])


class Command(object):
    def handle(self, *args):
        pass

    def handle_message(self, *args):
        pass


class GoogleHandler(Command):
    def __init__(self):
        self.browser = mechanize.Browser()
        # self.browser.addheaders = [('User-Agent', 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 5.1)')]
        self.browser.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1')]
        self.browser.set_handle_robots(False)

    def handle(self, bot, message, cmd, args):
        if cmd not in ('tits', 'show1', 'show'):
            return False

        bot.sendChatAction(message.chat_id, telegram.ChatAction.TYPING)

        P1 = ['', '', '', '', 'sexy', 'nice', 'girl', 'big', 'сочные', 'большие', 'женские']
        P2 = ['tits', 'boobs', 'boobies', 'сиськи', 'сисечки', 'титьки']

        # start = int(random() * 60)
        # Default: random from first 30 results
        start = int(random() * 26)

        if cmd == 'tits':
            cmd = 'show'
            args = choice(P1) + ' ' + choice(P2)
            # args = 'сиськи'
        else:
            if len(args.strip()) == 0:
                raise Exception('Введіть, що собсно шукати.')
            args = args.encode('utf-8')

        if cmd == 'show1':
            # Random from first 8 results
            cmd = 'show'
            start = int(random() * 4)

        if cmd == 'show':
            # response = self.browser.open('https://www.google.com/search?tbm=isch&q={}'.format(args.replace(' ', '+')))
            attempt = 0
            while True:
                if attempt == 3:
                    raise Exception('Я пробувала знайти картинки декілька разів, але не вдалося :( спробуй ще раз!')
                try:
                    response = self.browser.open(u'https://ajax.googleapis.com/ajax/services/search/images?v=1.0&{}&start={}'.format(
                        urlencode(dict(q=args)),
                        start
                    ))
                    data = response.read()
                    response = json.loads(data)
                    results = response['responseData']['results']
                    result = choice(results)
                    # title = urlencode(dict(d=result['title'].encode('utf-8')))[2:]
                    title = result['title'].encode('utf-8')
                    bot.sendChatAction(message.chat_id, telegram.ChatAction.UPLOAD_PHOTO)
                    bot.sendPhoto(chat_id=message.chat_id, photo=result['url'], caption=strip_tags(title))
                    return True
                    break
                except Exception as e:
                    attempt += 1


class FooHandler(Command):
    def handle(self, bot, message, cmd, args):
        if cmd == 'foo':
            bot.sendMessage(chat_id=message.chat_id, text='Bar')
            return True


class Pasta(Command):
    def __init__(self):
        self.browser = mechanize.Browser()

    def handle(self, bot, message, cmd, args):
        if cmd == 'pasta':
            response = self.browser.open('http://kopipasta.ru/random/all/all/desc/')
            soup = BeautifulSoup(response.read())
            links = soup.find_all('a', {'class': ['link-name']})
            link = choice(links)
            href = link['href']
            title = link.text
            content = strip_tags(link.parent.parent.find_all('div', {'class': 'article'})[-1].text).strip()

            if len(content) > 160:
                content = content[:160] + '...'

            text = u'**{}**\n > {}\nПовна версія: {}'.format(title, content, href)

            bot.sendMessage(chat_id=message.chat_id, text=text, parse_mode='Markdown')
            return True


class Stats(Command):
    def __init__(self):
        self.db = DB()
        self.db.upsert('stats', [
            ('username', 'varchar(64)'),
            ('message_count', 'int'),
        ])

    def handle(self, bot, message, cmd, args):
        if cmd == 'stats':
            result = self.db.select('SELECT * FROM stats ORDER BY message_count DESC LIMIT 5')
            bot.sendMessage(
                chat_id=message.chat_id,
                text='Топ-10 спамерів:\n\n' + '\n'.join(
                    [
                        '**{}** ({} повідомлень)'.format(row[1], row[2])
                        for row
                        in result
                        ]
                ),
                parse_mode='Markdown'
            )
            return True
        else:
            self.increase(message)

    def handle_message(self, bot, message):
        self.increase(message)

    def increase(self, message):
        if not isinstance(message.chat, telegram.GroupChat):
            return

        result = self.db.select('SELECT * FROM stats WHERE username = "{}"'.format(message.from_user.username))
        if not result:
            self.db.execute('INSERT INTO stats(username, message_count) VALUES("{}", {})'.format(
                message.from_user.username,
                1
            ))
        else:
            self.db.execute('UPDATE stats SET message_count = message_count + 1 WHERE username = "{}"'.format(
                message.from_user.username
            ))


class Fortune(Command):
    def handle(self, bot, message, cmd, args):
        if cmd == 'fortune':
            browser = mechanize.Browser()
            browser.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')]
            browser.set_handle_robots(False)
            response = browser.open('https://helloacm.com/api/fortune/')
            text = response.read().replace('\\t', '').replace('\\n', '\n').replace('\\"', '"').replace('\\\'', '\'').strip('"')

            translated = u'@{}: {}'.format(
                message.from_user.username,
                '\n'.join([translate('en', 'uk', line) for line in text.split('\n')])
            )

            bot.sendMessage(chat_id=message.chat_id, text=translated)
            return True
