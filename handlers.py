# coding: utf-8

from __future__ import print_function
import os
import urllib

import telegram
import mechanize
import re
from urllib import urlencode
from random import choice, random
import urllib2
from bs4 import BeautifulSoup
import time
from db import db, stars
import json
from HTMLParser import HTMLParser
import math
import configurator
import vk
from random import choice, random
import datetime
import traceback


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
    doc = BeautifulSoup(response.read())
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
                text='**{}**: {}'.format(str(e.__class__.__name__), str(e)),
                parse_mode='Markdown'
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
                    results = response['responseData']['results']
                    result = choice(results)
                    # title = urlencode(dict(d=result['title'].encode('utf-8')))[2:]
                    title = result['title'].encode('utf-8')
                    engine.telegram.sendChatAction(message.chat_id, telegram.ChatAction.UPLOAD_PHOTO)
                    engine.telegram.sendPhoto(chat_id=message.chat_id, photo=result['url'], caption=strip_tags(title))
                    return True
                    break
                except Exception as e:
                    attempt += 1

    handle_show1 = handle_show
    handle_tits = handle_show


class TitsBoobsHelper(Command):
    def handle_boobs(self, engine, message, cmd, args):
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
            soup = BeautifulSoup(response.read())
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
    def __init__(self):
        self.db = db
        self.db.upsert('stats', [
            ('username', 'varchar(64)'),
            ('message_count', 'int'),
        ])

        self.start_time = datetime.datetime.now()
        self.version = os.popen('git rev-parse HEAD').read().strip()
        self.last_commit = os.popen('git log --pretty=format:%cd').read().split('\n')[0]

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

    def handle_stats(self, engine, message, cmd, args):
        if cmd == 'stats':
            result = self.db.select('SELECT * FROM stats ORDER BY message_count DESC LIMIT 5')
            counts = self.db.select('SELECT COUNT(*) FROM stats UNION SELECT COUNT(*) FROM facts')
            stars_count = stars.select('SELECT COUNT(*) FROM stars')
            engine.telegram.sendMessage(
                chat_id=message.chat_id,
                text=u'Топ-5 спамерів:\n\n' + '\n'.join(
                    [
                        u'@{} (**{}** повідомлень)'.format(row[1], row[2])
                        for row
                        in result
                        ]
                ) + u'\n\nВ базі **{}** юзер(ів) і **{}** упоротий(х) факт(ів).\nПроіндексовано **{}** порнозірок з XVideos.\n\nКрім того, доводимо до вашого відома, що {}.\n\n{}'.format(
                    counts[0][0],
                    counts[1][0],
                    stars_count[0][0],
                    self.get_fact(),
                    self.get_version()
                ),
                parse_mode='Markdown'
            )
            return True
        else:
            self.increase(message)

    def handle_message(self, engine, message):
        self.increase(message)

    def increase(self, message):
        if not isinstance(message.chat, telegram.GroupChat):
            return

        if not message.from_user.username:
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

            translated = u'- {}: {}'.format(
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
                data = BeautifulSoup(urllib2.urlopen('http://www.xvideos.com/new/{}'.format(id)).read())
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


class VKAudioHandler(Command):
    def __init__(self):
        self.busy = False
        self.vkapi = vk.api
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

    def handle_music(self, engine, message, cmd, args, roll=False):
        if self.busy:
            raise Exception('Я зайнята, дайте мені дозалити поточний файл!')
        self.busy = True

        try:

            engine.telegram.sendChatAction(message.chat_id, telegram.ChatAction.TYPING)

            if len(args.strip()) == 0:
                raise Exception('Введіть, що собсно шукати.')
            result = self.vkapi.request('audio.search', q=args, v=5.37)

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
