# coding: utf-8

from __future__ import print_function
import os
from tempfile import NamedTemporaryFile
import textwrap
import urllib
from base64 import b64encode

import telegram
import mechanize
import re
from urllib import urlencode
import urllib2
from bs4 import BeautifulSoup
import time
from telegram.inlinequeryresult import (
    InlineQueryResultArticle,
    InlineQueryResultPhoto
)
from custom import InlineQueryResultAudio
from db import db, stars
import json
from HTMLParser import HTMLParser
import math
import configurator
import vk
from random import choice, random
import datetime
import traceback
from imgurpython import ImgurClient
import query3
from PIL import Image, ImageDraw, ImageFont


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
    browser.addheaders = [
        ('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')
    ]
    browser.set_handle_robots(False)
    browser.open('https://translate.google.com')
    browser.select_form(nr=0)

    browser.form['sl'] = [src]
    browser.form['tl'] = [dest]
    browser.form['text'] = text
    response = browser.submit()
    doc = BeautifulSoup(response.read(), 'lxml')
    return ''.join([x.text for x in doc.select('span#result_box > span')])


class Command(object):
    last_call = 0

    def throttle(self, amount):
        now = time.time()
        time_left = self.last_call + amount - now
        if time_left > 0:
            raise Exception(
                'Зачекайте ще {} секунд(и), перш ніж викликати цю команду знов.'.format(
                    int(math.ceil(time_left))
                )
            )
        self.last_call = time.time()

    def handle(self, engine, message, cmd, args):
        method_name = 'handle_{}'.format(cmd)
        try:
            getattr(self, method_name)(engine, message, cmd, args)
        except Exception as e:
            traceback.print_exc()
            engine.telegram.sendMessage(
                chat_id=message.chat_id,
                text='{}: {}'.format(str(e.__class__.__name__), str(e)),
                parse_mode=None
            )


class GenericHandler(Command):
    def handle_stop(self, engine, message, cmd, args):
        engine.telegram.sendMessage(chat_id=message.chat_id, text='Bye!')
        engine.stop()


class GoogleHandler(Command):
    P1 = ['', '', '', '', 'sexy', 'nice', 'girl', 'big', 'сочные', 'большие', 'женские']
    P2 = ['tits', 'boobs', 'boobies', 'сиськи', 'сисечки', 'титьки']

    def __init__(self):
        self.browser = mechanize.Browser()
        # self.browser.addheaders = [('User-Agent', 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 5.1)')]
        self.browser.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1')
        ]
        self.browser.set_handle_robots(False)

    def handle_show(self, engine, message, cmd, args):
        if cmd not in ('tits', 'show1', 'show'):
            return False

        engine.telegram.sendChatAction(message.chat_id, telegram.ChatAction.TYPING)

        start = int(random() * 26)

        if cmd == 'tits':
            cmd = 'show'
            args = choice(GoogleHandler.P1) + ' ' + choice(GoogleHandler.P2)
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
                    response = self.browser.open(
                        u'https://ajax.googleapis.com/ajax/services/search/images?v=1.0&{}&start={}'.format(
                            urlencode(dict(q=args)),
                            start
                        ))
                    data = response.read()
                    response = json.loads(data)
                    print(response)
                    results = response['responseData']['results']
                    result = choice(results)
                    # title = urlencode(dict(d=result['title'].encode('utf-8')))[2:]
                    title = result['title'].encode('utf-8')
                    engine.telegram.sendChatAction(message.chat_id, telegram.ChatAction.UPLOAD_PHOTO)
                    engine.telegram.sendPhoto(chat_id=message.chat_id, photo=result['url'], caption=strip_tags(title))
                    return True
                    break
                except Exception as e:
                    print('Google error')
                    traceback.print_exc()
                    attempt += 1

    handle_show1 = handle_show
    handle_tits = handle_show


class TitsBoobsHandler(Command):
    def handle_boobs(self, engine, message, cmd, args):
        return self.get('boobs', engine, message, cmd, args)

    def handle_tits(self, engine, message, cmd, args):
        return self.get('boobs', engine, message, cmd, args)

    def handle_butts(self, engine, message, cmd, args):
        return self.get('butts', engine, message, cmd, args)

    def get(self, source, engine, message, cmd, args):
        engine.telegram.sendChatAction(message.chat_id, telegram.ChatAction.TYPING)

        response = urllib2.urlopen('http://api.o{}.ru/noise/1'.format(source))
        data = json.loads(response.read())[0]

        engine.telegram.sendChatAction(message.chat_id, telegram.ChatAction.UPLOAD_PHOTO)

        engine.telegram.sendPhoto(
            chat_id=message.chat_id,
            photo='http://media.o{}.ru/{}'.format(
                source, data['preview'].replace('_preview', '')
            )
        )

    handle_boob = handle_boobs
    handle_butt = handle_butts


class RealGirlsHandler(Command):
    def subreddit(self, source, engine, message, cmd, args):
        engine.telegram.sendChatAction(message.chat_id, telegram.ChatAction.TYPING)
        client = ImgurClient(configurator.get('IMGUR_KEY'), configurator.get('IMGUR_SECRET'))

        gallery = client.subreddit_gallery(source, sort='new', window='all', page=int(random() * 30))
        gallery = filter(lambda item: item.size > 0, gallery)

        print(gallery)

        attempt = 0
        while attempt < 3:
            item = choice(gallery)

            engine.telegram.sendChatAction(message.chat_id, telegram.ChatAction.UPLOAD_PHOTO)

            print(message.chat_id)
            print(item.link)
            print(item.title)

            tf = NamedTemporaryFile(delete=False, suffix=item.link.split('.')[-1])
            img = urllib2.urlopen(item.link).read()
            tf.write(img)
            tf.close()

            try:
                engine.telegram.sendPhoto(
                    chat_id=message.chat_id,
                    photo=open(tf.name, 'r'),
                    # photo='https://www.google.com.ua/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png',
                    # caption=item.title
                )
                os.unlink(tf.name)
                return True
            except:
                os.unlink(tf.name)
                attempt += 1
        engine.telegram.sendMessage(chat_id=message.chat_id, text='Я тричі спробувала отримати картинку, але сталася якась помилка в API telegram :(')

        return True

    def handle_realgirl(self, engine, message, cmd, args):
        return self.subreddit('RealGirls', engine, message, cmd, args)

    def handle_amateur(self, engine, message, cmd, args):
        return self.subreddit('Amateur', engine, message, cmd, args)

    def handle_nsfw(self, engine, message, cmd, args):
        return self.subreddit('nsfw', engine, message, cmd, args)

    handle_realgirls = handle_realgirl


class FooHandler(Command):
    def handle_foo(self, engine, message, cmd, args):
        engine.telegram.sendMessage(chat_id=message.chat_id, text='Bar')
        return True


class Pasta(Command):
    def __init__(self):
        self.browser = mechanize.Browser()

    def handle_pasta(self, engine, message, cmd, args):
        if cmd == 'pasta':
            response = self.browser.open('http://kopipasta.ru/random/all/all/desc/')
            soup = BeautifulSoup(response.read(), 'lxml')
            links = soup.find_all('a', {'class': ['link-name']})
            link = choice(links)
            href = link['href']
            title = link.text
            content = strip_tags(link.parent.parent.find_all('div', {'class': 'article'})[-1].text).strip()

            if len(content) > 160:
                content = content[:160] + '...'

            text = u'**{}**\n > {}\nПовна версія: {}'.format(title, content, href)

            engine.telegram.sendMessage(chat_id=message.chat_id, text=text, parse_mode='Markdown')
            return True


class Stats(Command):
    META = {
        100: u'{} щойно написав своє соте повідомлення! ГЦ!',
        228: u'в {} вжу 228 меседжів! Є-й!',
        322: u'в {} вжу 322 меседжі! Є-й!',
        500: u'{} щойно написав своє п`ятсоте повідомлення! ГЦ!',
        1000: u'{} щойно написав своє тисячне повідомлення! ГЦ!',
        1337: u'1337 повідомлень в {}! Бокал віна цьому гаспадіну!',
        1488: u'{} щойно написав своє 1488-е повідомлення! SIEG HEIL!',
        1990: u'{} щойно написав своє 1990-е повідомлення! ROAD TO 2K!',
        2000: u'{} написав 2000-е повідомлення! Піздец. Зроби щось корисне :P',
        2500: u'{} написав 2500-е повідомлення! СЛОООЖНАААА',
        3000: u'{} написав 3000-е повідомлення! Це як десять трактористів АЗАЗАЗАЗ.',
        4000: u'{} написав 4000-е повідомлення! Ізі для вєлічайшего!',
        5000: u'{} написав 5000-е повідомлення! Саме стільки важить твоя мамка АЗАЗЗАЗАЗЗА.',
        9001: u'В {} вже OVER NINE THOUSAND меседжів. ДЕВ`ЯТЬ ТИСЯЧ, КАРЛ!',
        10000: u'{} НАХУЯРИВ 10к ПОВІДОМЛЕНЬ!!! Ти - про! ГЦ!',
    }

    TITLES = (
        u'The Boss',
        u'Carry',
        u'Аматор',
        u'Сапорт',
        u'Кур\'єр'
    )

    def __init__(self):
        self.db = db
        self.db.upsert('stats', [
            ('username', 'varchar(64)'),
            ('message_count', 'int'),
            ('chat_id', 'int'),
        ])
        self.db.upsert('messages', [
            ('username', 'varchar(64)'),
            ('chat_id', 'int'),
            ('message', 'text'),
            ('date_added', 'timestamp default current_time'),
        ])

        self.start_time = datetime.datetime.now()
        self.version = os.popen('git rev-parse HEAD').read().strip()
        self.last_commit = os.popen('git log --pretty=format:%cd').read().split('\n')[0]

    def get_fact(self, chat_id):
        results = db.select('SELECT text FROM facts ORDER BY RANDOM() LIMIT 1')
        if not results:
            raise Exception('В базі ще немає жодного факту :(')
        users = db.select('SELECT username FROM stats WHERE chat_id = ? ORDER BY RANDOM() LIMIT 5', (chat_id,))
        if not users or len(users) < 3:
            raise Exception('Недостатньо людей в базі :(')
        result = results[0][0]
        users = [u'@{}'.format(user[0]) for user in users]
        return result.format(*users)

    def handle_stats(self, engine, message, cmd, args):
        if cmd == 'stats':
            result = self.db.select('SELECT * FROM stats WHERE chat_id = ? ORDER BY message_count DESC LIMIT 5', (message.chat.id,))
            counts = self.db.select('SELECT COUNT(*) FROM stats UNION SELECT COUNT(*) FROM facts')
            total_all = self.db.select('SELECT SUM(message_count) FROM stats')
            stars_count = stars.select('SELECT COUNT(*) FROM stars')
            engine.telegram.sendMessage(
                chat_id=message.chat_id,
                text=u'Топ-5 спамерів:\n\n' + '\n'.join(
                    [
                        u'@{} (**{}** повідомлень) - {}'.format(row[1], row[2], Stats.TITLES[i])
                        for i, row
                        in enumerate(result)
                        ]
                ) + u'\n\nВсього написано як мінімум {} повідомлень.\nВ базі **{}** юзер(ів) і **{}** упоротий(х) факт(ів).\nПроіндексовано **{}** порнозірок з XVideos.\n\nКрім того, доводимо до вашого відома, що {}.\n\n{}'.format(
                    total_all[0][0],
                    counts[0][0],
                    counts[1][0],
                    stars_count[0][0],
                    self.get_fact(message.chat.id),
                    self.get_version()
                ),
                parse_mode='Markdown'
            )
            return True
        else:
            self.increase(engine, message)

    def handle_message(self, engine, message):
        self.db.execute('INSERT INTO messages(username, chat_id, message) VALUES(?, ?, ?)', (
            message.from_user.username or message.from_user.id,
            message.chat.id,
            message.text
        ))

        self.increase(engine, message)

    def increase(self, engine, message):
        if message.chat.id > 0:
            return

        if not message.from_user.username:
            return

        result = self.db.select('SELECT * FROM stats WHERE username = "{}"'.format(message.from_user.username))
        if not result:
            self.db.execute('INSERT INTO stats(username, message_count, chat_id) VALUES("{}", {}, {})'.format(
                message.from_user.username,
                1,
                message.chat.id
            ))
            count = 1
        else:
            self.db.execute('UPDATE stats SET message_count = message_count + 1 WHERE username = "{}"'.format(
                message.from_user.username
            ))
            count = self.db.select('SELECT message_count FROM stats WHERE username = "{}"'.format(
                message.from_user.username
            ))[0][0]
        congrats = Stats.META.get(int(count), None)
        if congrats:
            engine.telegram.sendMessage(
                chat_id=message.chat_id,
                text=congrats.format('@{}'.format(message.from_user.username))
            )

    def handle_version(self, engine, message, cmd, args):
        engine.telegram.sendMessage(
            chat_id=message.chat_id,
            text=self.get_version(),
            parse_mode='Markdown'
        )
        return True

    def get_version(self):
        return u'- Версія бота: {} ({})\n- Останній перезапуск бота: {}'.format(
            self.version,
            self.last_commit,
            self.start_time,
        )


class Fortune(Command):
    def handle_fortune(self, engine, message, cmd, args):
        if cmd == 'fortune':
            self.throttle(5)

            browser = mechanize.Browser()
            browser.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')]
            browser.set_handle_robots(False)
            response = browser.open('https://helloacm.com/api/fortune/')
            text = response.read().replace(
                '\\t', ''
            ).replace(
                '\\n', '\n'
            ).replace(
                '\\"', '"'
            ).replace(
                '\\\'', '\''
            ).strip('"')

            translated = u'@{}: {}'.format(
                message.from_user.username,
                '\n'.join([translate('en', 'uk', line) for line in text.split('\n')])
            )

            engine.telegram.sendMessage(chat_id=message.chat_id, text=translated)
            return True


class DotaRandom(Command):
    def handle_ar(self, engine, message, cmd, args):
        if cmd == 'ar':
            browser = mechanize.Browser()
            browser.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')]
            browser.set_handle_robots(False)
            response = browser.open('http://www.dota2.com/heroes/?l=ukrainian')
            soap = BeautifulSoup(response.read(), 'lxml')

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
            engine.telegram.sendPhoto(
                chat_id=message.chat_id,
                photo='http://cdn.dota2.com/apps/dota2/images/heroes/{}_full.png'.format(hero_id),
                caption=hero_names[hero_id] + '!'
            )


class Roll(Command):
    def handle_roll(self, engine, message, cmd, args):
        if cmd == 'roll':
            result = choice([1, 2, 3, 4, 5, 6] * 5 + ['Кубік проєбався! Беремо новий...'])
            if isinstance(result, int):
                result = 'Випало "{}"!'.format(result)
            engine.telegram.sendMessage(
                chat_id=message.chat_id,
                text='@{} кидає кубик... {}'.format(message.from_user.username, result)
            )
            return True


class Questions(Command):
    def handle_q(self, engine, message, cmd, args):
        if cmd == 'q':
            result = choice(['так', 'ні', '17%, що так', 'нє, ніхуя', 'спитай шось попрощє', 'а хуй його знає'])
            engine.telegram.sendMessage(
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

    def handle_fact(self, engine, message, cmd, args):
        if cmd == 'fact':
            results = db.select('SELECT text FROM facts ORDER BY RANDOM() LIMIT 1')
            if not results:
                raise Exception('В базі ще немає жодного факту :(')
            users = db.select('SELECT username FROM stats ORDER BY RANDOM() LIMIT 5')
            if not users or len(users) < 3:
                raise Exception('Недостатньо людей в базі :(')
            result = results[0][0]
            users = [u'@{}'.format(user[0]) for user in users]
            engine.telegram.sendMessage(
                chat_id=message.chat_id,
                text=result.format(*users)
            )
            return True
        elif cmd == 'factlist':
            results = db.select('SELECT text FROM facts')
            if not results:
                raise Exception('В базі ще немає жодного факту :(')

            engine.telegram.sendMessage(
                chat_id=message.chat_id,
                text=u'Всі факти:\n\n' + '\n'.join(
                    [
                        u'{}'.format(row[0])
                        for row
                        in results
                        ]
                ),
                parse_mode='Markdown'
            )
            return True
        elif cmd == 'addfact':
            if len(args.strip()) == 0:
                raise Exception('Введіть, що саме додати! Наприклад: "/addfact {} любить фапати на аніме.".')
            if args.find('{}') == -1:
                raise Exception('В факті має бути принаймні одна і не більше п’яти пар фігурних дужок - "{}".')
            if args.count('{}') > 3:
                raise Exception('В факті має бути принаймні одна і не більше трьох пар фігурних дужок - "{}".')
            self.db.execute(
                'INSERT INTO facts(author, text) VALUES("{}", ?)'.format(message.from_user.username),
                (args.strip(),)
            )
            engine.telegram.sendMessage(
                chat_id=message.chat_id,
                text='Факт додано!'
            )

    handle_addfact = handle_fact
    handle_factlist = handle_fact


class PornRoll(Command):
    def handle_redroll(self, engine, message, cmd, args):
        self.throttle(2)

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
                engine.telegram.sendPhoto(
                    chat_id=message.chat_id,
                    photo=cover_url,
                    caption='{}: {}'.format(video_title, url)
                )
                return True

            attempts += 1

    def handle_xroll(self, engine, message, cmd, args):
        self.throttle(2)

        attempts = 0

        while True:
            if attempts > 3:
                raise Exception('Please try again :/')

            try:
                id = int(random() * 100000)
                data = BeautifulSoup(urllib2.urlopen('http://www.xvideos.com/new/{}'.format(id)).read(), 'lxml')
            except:
                pass
            else:
                blocks = data.find_all('div', {'class': ['thumbBlock']})
                block = choice(blocks)
                img = block.find('img')
                if img:
                    cover_url = block.find('img')['src']
                    title = block.find('p').find('a').text
                    url = block.find('a')['href']
                else:
                    script = block.find('script').text
                    cover_url = re.findall('img[\s]*src="([^"]+)"', script)[0]
                    title = re.findall('title[\s]*=[\s]*"([^"]+)"', script)[0]
                    url = re.findall('a[\s]*href="([^"]+)"', script)[0]

                cover_url = cover_url.replace('/thumbs/', '/thumbslll/')

                duration = block.find('span', {'class': ['duration']}).text

                engine.telegram.sendPhoto(
                    chat_id=message.chat_id,
                    photo=cover_url,
                    caption='{} {}: {}'.format(
                        title,
                        duration,
                        'http://www.xvideos.com/{}'.format(url.lstrip('/'))
                    )
                )
                return True

            attempts += 1


class Stars(Command):
    def handle_star(self, engine, message, cmd, args):
        slug, name, video_count, poster_url = stars.select('SELECT * FROM stars ORDER BY RANDOM() LIMIT 1')[0]
        engine.telegram.sendPhoto(
            chat_id=message.chat_id,
            photo=poster_url,
            caption='{} ({} videos): {}'.format(
                name,
                video_count,
                'http://www.xvideos.com/profiles/{}#_tabVideos,videos-best'.format(slug)
            )
        )
        return True


class BarrelRollHandler(Command):
    def handle_barrelroll(self, engine, message, cmd, args):
        if cmd == 'barrelroll':
            self.throttle(30)
            engine.telegram.sendAudio(
                chat_id=message.chat_id,
                audio=open('./res/roll.mp3', 'rb'),
                title='Do the barrel roll!'
            )
            return True


class AdminHandler(Command):
    def handle_say_admin(self, engine, message, cmd, args):
        engine.telegram.sendMessage(
            chat_id=configurator.get('CHAT_ID'),
            text=args
        )

    def handle_message(self, engine, message):
        if message.chat_id > 0:
            if message.sticker:
                engine.telegram.sendMessage(
                    chat_id=message.chat_id,
                    text=str(message.sticker)
                )


class _VKAudioHandler(Command):
    def handle_music(self, *args):
        raise Exception('Ця команда застаріла. Пишіть @nyashbot <назва треку>')


class VKAudioHandler(Command):
    def __init__(self):
        self.need_captcha = False
        self.message = None
        self.cmd = None
        self.args = None
        self.roll = None

        self.vkapi = vk.api
        self.busy = True
        self.login()
        self.busy = False

    def login(self):
        print('Trying to authorize at VK...')
        login_result = self.vkapi.log_in(
            configurator.get('VK_LOGIN'),
            configurator.get('VK_PASS'),
            configurator.get('VK_APP_ID'),
            'audio'
        )
        if login_result:
            print('VK auth succeeded!')
        else:
            print('VK auth failed.')
        self.last_login = time.time()

    def handle_captcha(self, engine, message, cmd, args):
        if not self.need_captcha:
            raise Exception('Капчу вже не потрібно, дякую :)')
        return self.handle_music(engine, self.message, self.cmd, self.args, roll=self.roll, captcha=cmd)

    def handle_music(self, engine, message, cmd, args, roll=False, captcha=None):
        if self.busy:
            raise Exception('Я зайнята, дайте мені дозалити поточний файл!')
        if self.need_captcha:
            raise Exception('Не можу здійснити пошук, доки ви не розв`яжете капчу!')
        self.busy = True

        if self.last_login < time.time() - 3600:
            self.login()

        try:
            engine.telegram.sendChatAction(message.chat_id, telegram.ChatAction.TYPING)

            if len(args.strip()) == 0:
                raise Exception('Введіть, що собсно шукати.')
            if captcha:
                result = self.vkapi.request('audio.search', q=args, v=5.37, captcha_sid=self.captcha_sid, captcha_key=captcha)
            else:
                result = self.vkapi.request('audio.search', q=args, v=5.37)

            if 'error' in result['response']:
                self.captcha_sid = result['error']['captcha_sid']
                engine.telegram.sendPhoto(
                    chat_id=message.chat_id,
                    photo=data['error']['captcha_img']
                )
                self.need_captcha = True
                self.message = message
                self.cmd = cmd
                self.args = args
                self.roll = roll
                return True

            self.need_captcha = False

            print(result)

            data = result['response']
            if not data['count']:
                raise Exception('Нічого не знайдено :(')

            if roll:
                first = choice(data['items'])
            else:
                first = data['items'][0]

            title = u'{} - {} ({}:{})'.format(
                first['artist'],
                first['title'],
                first['duration'] / 60,
                str(first['duration'] % 60).rjust(2, '0')
            )

            engine.telegram.sendChatAction(message.chat_id, telegram.ChatAction.UPLOAD_AUDIO)

            response = urllib.urlopen(first['url'])
            fname = '/tmp/vk-{}.mp3'.format(str(int(random() * 1000000)))
            f = open(fname, 'wb')
            f.write(response.read())
            f.close()

            f = open(fname, 'rb')

            engine.telegram.sendAudio(chat_id=message.chat_id, audio=f, title=title.encode('utf-8'))

            os.remove(fname)

            self.busy = False
        except:
            # Prevent deadlock
            self.busy = False
            raise

    def handle_musicroll(self, engine, message, cmd, args):
        return self.handle_music(engine, message, cmd, args, True)


class UTHandler(Command):
    def __init__(self):
        self.conn = query3.Connection()
        self.wiki = 'http://liandri.beyondunreal.com'

        self.new_mode = None

    def request(self, command, data=None):
        request = urllib2.Request('http://dun.ai:8075/ServerAdmin/{}'.format(command), urllib.urlencode(data) if data else None)
        request.add_header('Authorization', 'Basic {}'.format(b64encode('{}:{}'.format(configurator.get('UT_ADMIN_LOGIN'), configurator.get('UT_ADMIN_PASSWORD')))))
        response = urllib2.urlopen(request)
        return BeautifulSoup(response.read(), 'lxml')

    def get_players(self):
        doc = self.request('current_players')

        trs = doc.select('form[action="current_players"] tr[align="left"]')

        names = [tr.find_all('td')[2].contents[0].encode('utf-8').replace('\xc2\xa0', ' ').strip() for tr in trs]

        bots = []
        players = []

        for name in names:
            if name.endswith('(Bot)'):
                bots.append(name.split(' ')[0])
            else:
                players.append(name)

        return (sum((len(bots), len(players))), players, bots)

    def build_menu(self, options):
        menu_items = [[]]

        for i, option in enumerate(options):
            menu_items[-1].append(option)
            if (i + 1) % 3 == 0:
                menu_items.append([])

        return menu_items

    def get_map_image(self, map_name_full):
        image = None

        try:
            parts = map_name_full.split('-')
            parts[-1] = parts[-1].capitalize()
            url = '{}/{}'.format(self.wiki, '-'.join(parts))
            response = urllib2.urlopen(url)
        except:
            pass
        else:
            doc = BeautifulSoup(response.read(), 'lxml')
            thumb = doc.find('img', {'class': ['thumbimage']})
            if thumb:
                image = self.wiki + '/' + thumb['src']

        return image

    def handle_ut_mode(self, engine, message, cmd, args):
        if args:
            self.new_mode = args

            doc = self.request('current_game', dict(SwitchGameType='Switch', MapSelect='', GameTypeSelect=args))
            options = ['/ut_map ' + option['value'] for option in doc.select('select[name="MapSelect"] option')]
            options.append('/cancel')

            menu_items = self.build_menu(options)

            engine.telegram.sendMessage(
                text='Вибрано режим: {}. Тепер виберіть карту:'.format(args),
                chat_id=message.chat_id,
                reply_to_message=message.message_id,
                reply_markup=telegram.ReplyKeyboardMarkup(
                    menu_items,
                    one_time_keyboard=True,
                    selective=True
                )
            )
        else:
            doc = self.request('current_game')
            options = ['/ut_mode ' + option['value'] for option in doc.select('select[name="GameTypeSelect"] option')]
            options.append('/cancel')

            menu_items = self.build_menu(options)

            engine.telegram.sendMessage(
                text='Виберіть режим гри:',
                chat_id=message.chat_id,
                reply_to_message=message.message_id,
                reply_markup=telegram.ReplyKeyboardMarkup(
                    menu_items,
                    one_time_keyboard=True,
                    selective=True
                )
            )

    def handle_ut_map(self, engine, message, cmd, args):
        if args:
            if self.new_mode:
                mapname = args

                self.request('current_game', dict(SwitchGameTypeAndMap='Switch', MapSelect=mapname, GameTypeSelect=self.new_mode))

                image = self.get_map_image(mapname)

                text = 'Сервер рестартується (зачекайте 10-15 секунд).\nРежим: {}\nКарта: {}'.format(self.new_mode, mapname)

                if image:
                    engine.telegram.sendPhoto(
                        chat_id=message.chat_id,
                        photo=image,
                        caption=text,
                    )
                else:
                    engine.telegram.sendMessage(
                        chat_id=message.chat_id,
                        text=text,
                        parse_mode=None
                    )

                self.new_mode = None
            else:
                raise Exception('Спершу виберіть режим гри ("/ut_mode")')
        else:
            pass

    def handle_ut(self, engine, message, cmd, args):
        info = self.conn.get_info()

        player_count, players, bots = self.get_players()

        info['player_count'] = player_count

        image = self.get_map_image(info['map_name'])

        info.update(dict(
            players=', '.join(players) if len(players) else '(no players)',
            bots_count=len(bots)
        ))

        text = 'Server: {host}:{port}\nGame type: {game_type}\nMap: {map_name}\nPlayers: {player_count}/{max_player_count}\n\nPlayers: {players}\nBots count: {bots_count}'.format(**info)

        if image:
            engine.telegram.sendPhoto(
                chat_id=message.chat_id,
                photo=image,
                caption=text,
            )
        else:
            engine.telegram.sendMessage(
                chat_id=message.chat_id,
                text=text,
                parse_mode=None
            )


class ResponseHandler(Command):
    # BQADBAADvAQAApv7sgAB-a10wug0trsC - OAGF
    # BQADBAADbAADXSupASBF4k8DAAHWowI - Harold
    # BQADAgADGgADVaMOAAFpsDjXHc8RCwI - Kappa
    # BQADAgADIQADVaMOAAE-mu2vH2C0RAI - Bratishka!
    # BQADAQADuQMAAiMzHAABz0nPM08joi8C - Hitler
    # BQADAgADIAADS0sKBf4vXb9s-tpQAg - Gaben
    # BQADAQADXgUAAiBWmALK7Xfe8O0gKAI - Just do it!
    # BQADAgADDAADj4_IB1ei99O6HjlzAg - Overlort
    # BQADAgADFwADEWUuCAI773bfgwSoAg - 322
    def match(self, string, patterns):
        string = string.lower()
        for pattern in patterns:
            if pattern.lower() in string.lower():
                return True
        return False

    def handle_message(self, engine, message):
        if self.match(message.text, ['))']):
            engine.telegram.sendSticker(
                chat_id=message.chat_id,
                sticker='BQADBAADbAADXSupASBF4k8DAAHWowI'
            )
        elif self.match(message.text, ['kappa',  u'каппа']):
            engine.telegram.sendSticker(
                chat_id=message.chat_id,
                sticker='BQADAgADGgADVaMOAAFpsDjXHc8RCwI'
            )
        elif self.match(message.text, ['bratishka', u'братішка', u'братишка']):
            engine.telegram.sendSticker(
                chat_id=message.chat_id,
                sticker='BQADAgADIQADVaMOAAE-mu2vH2C0RAI'
            )
        elif self.match(message.text, ['1488', '14/88']):
            engine.telegram.sendSticker(
                chat_id=message.chat_id,
                sticker='BQADAQADuQMAAiMzHAABz0nPM08joi8C'
            )
        elif self.match(message.text, ['gabe', u'гейб', u'габен']):
            engine.telegram.sendSticker(
                chat_id=message.chat_id,
                sticker='BQADAgADIAADS0sKBf4vXb9s-tpQAg'
            )
        elif self.match(message.text, ['do it', 'go!', 'goo', u'го!', u'го1', u'гоо']):
            engine.telegram.sendSticker(
                chat_id=message.chat_id,
                sticker='BQADAQADXgUAAiBWmALK7Xfe8O0gKAI'
            )
        elif self.match(message.text, [u'підор', u'підар', 'pidor', 'pidar']):
            engine.telegram.sendSticker(
                chat_id=message.chat_id,
                sticker='BQADAgADDAADj4_IB1ei99O6HjlzAg'
            )
        elif self.match(message.text, ['322']):
            engine.telegram.sendSticker(
                chat_id=message.chat_id,
                sticker='BQADAgADFwADEWUuCAI773bfgwSoAg'
            )


class PhrasesHandler(Command):
    def __init__(self):
        f = open('phrases.txt', 'r')
        self.phrases = filter(None, f.read().split('\n'))
        f.close()

    def handle_phrase(self, engine, message, cmd, args):
        engine.telegram.sendMessage(
            chat_id=message.chat_id,
            text='@{}, {}!'.format(message.from_user.username, choice(self.phrases))
        )


class CancelHandler(Command):
    def handle_cancel(self, engine, message, cmd, args):
        engine.telegram.sendMessage(
            text='Скасовано.',
            chat_id=message.chat_id,
            reply_to_message=message.message_id,
            reply_markup=telegram.ReplyKeyboardHide(
                selective=True
            )
        )
        return True


class InlineAudioHandler(Command):
    def __init__(self):
        self.last_login = 0
        self.vkapi = vk.VKApi()
        self.login()

    def login(self):
        print('Trying to authorize at VK...')
        login_result = self.vkapi.log_in(
            configurator.get('VK_LOGIN'),
            configurator.get('VK_PASS'),
            configurator.get('VK_APP_ID'),
            'audio'
        )
        if login_result:
            print('VK auth succeeded!')
        else:
            print('VK auth failed.')
        self.last_login = time.time()

    def handle_inline(self, engine, inline_query):
        result = self.vkapi.request('audio.search', q=inline_query.query, v=5.37)
        items = result['response']['items']

        engine.telegram.answerInlineQuery(inline_query.id, [
            InlineQueryResultAudio(long(time.time() * 1000000), t['url'], 'audio/mp3', t['artist'].strip(), t['title'].strip())
            for t
            in items[:10]
        ])


class MemeHandler(Command):
    # def handle_gen(self, engine, message, cmd, args):
    def handle_inline(self, engine, inline_query):
        text = inline_query.query
        # parts = filter(None, message.text.split(' '))
        # if len(parts) < 3:
        #     engine.telegram.sendMessage(
        #         text='Інструкція:\n/gen image_name Текст для відображення.\nДоступні зображення:\n{}'.format(
        #             '\n'.join('{}'.format('.'.join(x.split('.')[:-1])) for x in os.listdir('./memes'))
        #         ),
        #         chat_id=message.chat_id,
        #         reply_to_message=message.message_id,
        #         reply_markup=telegram.ReplyKeyboardHide(
        #             selective=True
        #         )
        #     )
        #     return

        URL = 'http://cs4739v4.vk.me/u1843971/audios/f4201aa0226b.mp3?extra=LCwf3s2KXKBogyul0zl4g7NqOc68x4Gt9xqPmHCsFltcZ-GRKm0xBaQPS6SmERwJkZoG6mfcU-_Dkn7ArSIWg-O2wRFt_ndr4HQisQ3MDZszL1RzdJGQ8m80kLfMLbNQNHf3qY2VSTsQ'

        engine.telegram.answerInlineQuery(inline_query.id, [
            InlineQueryResultAudio(long(time.time() * 1000000), URL, 'audio/mp3', 'Test', 'Song123!')
        ])
        return

        parts = text.split(' ')

        if len(parts) < 2:
            engine.telegram.answerInlineQuery(inline_query.id, [
                InlineQueryResultArticle(long(time.time() * 1000000), 'Можливий варіант: ' + '.'.join(x.split('.')[:-1]), ':/')
                for x
                in os.listdir('./memes')
            ])
            return True

        name = parts[0]
        texts = filter(None, [x.strip() for x in ' '.join(parts[1:]).split(';')])
        try:
            meta_file = open('./memes/{}.json'.format(name))
            meta = json.loads(meta_file.read())
            meta_file.close()
        except:
            engine.telegram.answerInlineQuery(inline_query.id, [
                InlineQueryResultArticle(long(time.time() * 1000000), 'Зображення "{}" не знайдено :('.format(name), ':/')
                ])
            return

        img = Image.open(meta['src'])
        draw = ImageDraw.Draw(img)
        text_color = meta['textColor']
        font_size = meta['fontSize']
        iw, ih = img.size

        font = ImageFont.truetype('./fonts/Roboto-Regular.ttf', size=font_size)
        # font = ImageFont.load('./fonts/Roboto-Regular.ttf')

        rects = meta['rects']

        for i, text in enumerate(texts):
            try:
                x, y, w, h = rects[i]
            except:
                continue

            avg_width = draw.textsize(text, font)[0] / len(text)

            chars_per_line = w / avg_width

            multiline = '\n'.join(textwrap.wrap(text, width=chars_per_line))

            mw, mh = draw.multiline_textsize(multiline, font)

            draw.multiline_text((x + w / 2 - mw / 2, y + h / 2 - mh / 2), multiline, fill=text_color, font=font, align='center')

        # img.show()

        # img.drawText()

        # tf = NamedTemporaryFile(delete=False, suffix='.jpg')
        # img.save(tf, format='JPEG', quality=92)
        # tf.close()
        #
        # f = open(tf.name, 'rb')

        s = str(long(time.time() * 1000000))

        img_name_full = '{}.jpeg'.format(s)
        img_name_thumb = '{}_thumb.jpeg'.format(s)

        img_path_full = configurator.get('IMG_DIR') + img_name_full
        img_path_thumb = configurator.get('IMG_DIR') + img_name_thumb

        img.save(img_path_full)
        img.thumbnail((160, 160), Image.LINEAR)
        img.save(img_path_thumb)

        # engine.telegram.sendPhoto(
        #     chat_id=message.chat.id,
        #     photo=f
        # )

        # print(dict(
        #     photo_url=configurator.get('IMG_HOST') + img_name_full,
        #     thumb_url=configurator.get('IMG_HOST') + img_name_thumb,
        # ))

        engine.telegram.answerInlineQuery(inline_query.id, [
            InlineQueryResultPhoto(
                long(time.time() * 1000000),
                photo_url=configurator.get('IMG_HOST') + img_name_full,
                thumb_url=configurator.get('IMG_HOST') + img_name_thumb,
                photo_width=iw,
                photo_height=ih
            )
        ])

        # os.unlink(tf.name)

        return True


class CarmaHandler(Command):
    def __init__(self):
        self.db = db
        self.db.upsert('carma', [
            ('username', 'varchar(64)'),
            ('commends', 'int'),
            ('reports', 'int'),
        ])
        self.db.upsert('feedbacks', [
            ('username', 'varchar(64)'),
            ('who', 'varchar(64)'),
            ('message', 'int'),
            ('rating', 'int')
        ])

    def submit_score(self, username, good):
        results = db.select(
            'SELECT * '
            'FROM carma WHERE username="{}"'.format(
                username
            )
        )
        if not results:
            db.execute(
                'INSERT INTO carma(username, commends, reports) '
                'VALUES("{}", 0, 0)'.format(username)
            )
            commends = 0
            reports = 0
        else:
            _, _, commends, reports = results[0]

        if good:
            commends += 1
        else:
            reports += 1

        db.execute(
            'UPDATE carma SET commends={}, reports={} '
            'WHERE username="{}"'.format(
                commends,
                reports,
                username
            )
        )

    def handle_report(self, engine, message, cmd, args):
        args = args.strip().strip('@')
        if args == message.from_user.username.strip('@'):
            raise Exception('Ніззя репортити/коммендити себе самого, дурнику!')
        if not len(args):
            raise Exception(
                'Введіть нік того, на кого бажаєте поскаржитись!'
                'Приклад: /report @megaspro'
            )
        self.submit_score(args, False)
        engine.telegram.sendMessage(
            text='Вашу скаргу прийнято. Дякуємо за те,'
            'що допомагаєте зробити спільноту Днота 2 кращою!',
            chat_id=message.chat_id
        )
        return True

    def handle_commend(self, engine, message, cmd, args):
        if not len(args):
            raise Exception(
                'Введіть нік того, кого бажаєте похвалити!'
                'Приклад: /commend @megaspro'
            )
        self.submit_score(args, True)
        engine.telegram.sendMessage(
            text='Ваш комменд прийнято!',
            chat_id=message.chat_id
        )
        return True

    def handle_carma(self, engine, message, cmd, args):
        username = message.from_user.username or message.from_user.id
        results = db.select(
            'SELECT * FROM carma '
            'WHERE username="{}"'.format(
                username
            )
        )
        if not len(results):
            raise Exception('Вас ще ніхто не комендив/репортив.')

        _, _, commends, reports = results[0]

        engine.telegram.sendMessage(
            text='Карма: {}\n{} репорт(ів), {} комменд(ів)'.format(
                commends - reports,
                reports,
                commends
            ),
            chat_id=message.chat_id
        )
