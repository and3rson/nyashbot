# coding: utf-8

from __future__ import print_function

import telegram
import mechanize
import re
from urllib import urlencode
from random import choice, random
import urllib2
from bs4 import BeautifulSoup
from db import db, stars
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
        self.db = db
        self.db.upsert('stats', [
            ('username', 'varchar(64)'),
            ('message_count', 'int'),
        ])


    def get_fact(self):
        results = db.select('SELECT text FROM facts ORDER BY RANDOM() LIMIT 1')
        if not results:
            raise Exception('В базі ще немає жодного факту :(')
        users = db.select('SELECT username FROM stats ORDER BY RANDOM() LIMIT 5')
        if not users or len(users) < 3:
            raise Exception('Недостатньо людей в базі :(')
        result = results[0][0]
        users = [u'@{}'.format(user[0]) for user in users]
        return result.format(*users)

    def handle(self, bot, message, cmd, args):
        if cmd == 'stats':
            result = self.db.select('SELECT * FROM stats ORDER BY message_count DESC LIMIT 5')
            counts = self.db.select('SELECT COUNT(*) FROM stats UNION SELECT COUNT(*) FROM facts')
            stars_count = stars.select('SELECT COUNT(*) FROM stars')
            bot.sendMessage(
                chat_id=message.chat_id,
                text='Топ-5 спамерів:\n\n' + '\n'.join(
                    [
                        '**{}** ({} повідомлень)'.format(row[1], row[2])
                        for row
                        in result
                        ]
                ) + '\n\nВ базі {} юзер(ів) і {} упоротий(х) факт(ів).\nПроіндексовано {} порнозірок з XVideos.\nКрім того, доводимо до вашого відома, що {}.'.format(
                    counts[0][0],
                    counts[1][0],
                    stars_count[0][0],
                    self.get_fact().encode('utf-8')
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


class DotaRandom(Command):
    def handle(self, bot, message, cmd, args):
        if cmd == 'ar':
            browser = mechanize.Browser()
            browser.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')]
            browser.set_handle_robots(False)
            response = browser.open('http://www.dota2.com/heroes/?l=ukrainian')
            soap = BeautifulSoup(response.read())

            filter_name = soap.find_all('select', {'id': ['filterName']})[0]
            hero_names = {
                option['value']: option.text
                for option
                in filter_name.find_all('option')[2:]
                }

            links = soap.find_all('a', {'class': ['heroPickerIconLink']})
            link = choice(links)
            parts = link['id'].split('_')[1:]
            hero_id = '_'.join(parts)
            bot.sendPhoto(
                chat_id=message.chat_id,
                photo='http://cdn.dota2.com/apps/dota2/images/heroes/{}_full.png'.format(hero_id),
                caption=hero_names[hero_id] + '!'
            )


class Roll(Command):
    def handle(self, bot, message, cmd, args):
        if cmd == 'roll':
            result = choice([1, 2, 3, 4, 5, 6] * 5 + ['Кубік проєбався! Беремо новий...'])
            if isinstance(result, int):
                result = 'Випало "{}"!'.format(result)
            bot.sendMessage(
                chat_id=message.chat_id,
                text='@{} кидає кубик... {}'.format(message.from_user.username, result)
            )
            return True


class Questions(Command):
    def handle(self, bot, message, cmd, args):
        if cmd == 'q':
            result = choice(['так', 'ні', '17%, що так', 'нє, ніхуя', 'спитай шось попрощє', 'а хуй його знає'])
            bot.sendMessage(
                chat_id=message.chat_id,
                text='@{}: {}'.format(message.from_user.username, result)
            )
            return True


class Facts(Command):
    def __init__(self):
        self.db = db
        self.db.upsert('facts', [
            ('author', 'varchar(64)'),
            ('text', 'text'),
        ])

    def handle(self, bot, message, cmd, args):
        if cmd == 'fact':
            results = db.select('SELECT text FROM facts ORDER BY RANDOM() LIMIT 1')
            if not results:
                raise Exception('В базі ще немає жодного факту :(')
            users = db.select('SELECT username FROM stats ORDER BY RANDOM() LIMIT 5')
            if not users or len(users) < 3:
                raise Exception('Недостатньо людей в базі :(')
            result = results[0][0]
            users = [u'@{}'.format(user[0]) for user in users]
            bot.sendMessage(
                chat_id=message.chat_id,
                text=result.format(*users)
            )
            return True
        elif cmd == 'addfact':
            if len(args.strip()) == 0:
                raise Exception('Введіть, що саме додати! Наприклад: "/addfact {} любить фапати на аніме.".')
            if args.find('{}') == -1:
                raise Exception('В факті має бути принаймні одна і не більше п’яти пар фігурних дужок - "{}".')
            if args.count('{}') > 3:
                raise Exception('В факті має бути принаймні одна і не більше трьох пар фігурних дужок - "{}".')
            self.db.execute('INSERT INTO facts(author, text) VALUES("{}", ?)'.format(message.from_user.username), (args.strip(),))
            bot.sendMessage(
                chat_id=message.chat_id,
                text='Факт додано!'
            )


class PornRoll(Command):
    def handle(self, bot, message, cmd, args):
        if cmd == 'pornroll':
            attempts = 0

            while True:
                if attempts > 3:
                    raise Exception('Please try again :/')
                try:
                    id = int(random() * 100000)
                    url = 'http://www.redtube.com/{}'.format(id)
                    request = urllib2.Request(url)
                    response = urllib2.urlopen(request)
                    data = response.read()
                except:
                    pass
                else:
                    cover_url = re.findall('poster: "([^"]+)"', data)
                    cover_url = cover_url[0].replace('\\/', '/')

                    video_title = re.findall('videoTitle: "([^"]+)"', data)
                    video_title = video_title[0].replace('\\/', '/')
                    bot.sendPhoto(chat_id=message.chat_id, photo=cover_url, caption='{}: {}'.format(video_title, url))
                    return True

                attempts += 1


class Stars(Command):
    def handle(self, bot, message, cmd, args):
        if cmd == 'star':
            slug, name, video_count, poster_url = stars.select('SELECT * FROM stars ORDER BY RANDOM() LIMIT 1')[0]
            bot.sendPhoto(
                chat_id=message.chat_id,
                photo=poster_url,
                caption='{} ({} videos): {}'.format(
                    name,
                    video_count,
                    'http://www.xvideos.com/profiles/{}#_tabVideos,videos-best'.format(slug)
                )
            )
            return True
