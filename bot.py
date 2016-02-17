#!/usr/bin/env python2.7
# coding: utf-8

from __future__ import print_function

from gevent import spawn, monkey

monkey.patch_socket()
monkey.patch_ssl()

import os
import sys
import re
import traceback
import telegram
import handlers
import tasks
import configurator
import random

try:
    import settings as settings_test
except ImportError:
    sys.stdout.write(
        "Please create settings.py file this code:\n\nTOKEN = '<YOUR_TOKEN>'\nCHAT_ID = <CHAT_NUMERIC_ID>\n\n"
    )


phrases = handlers.PhrasesHandler()


class Scheduler(object):
    def __init__(self):
        pass


class Bot(object):
    def __init__(self):
        self.telegram = telegram.Bot(token=configurator.get('TOKEN'))
        self.initial = True
        self.id = 0
        self.handlers = []
        self.terminated = False

    def add_handlers(self, *args):
        for handler in args:
            self.handlers.append(handler)

    def handle_update(self, update):
        message = update.message
        match = re.findall('^/([a-zA-Z_0-9]+)(\s+(.+$))?', message.text.strip())

        if match:
            match = match[0]
            cmd = match[0].lower()
            args = match[2]
            method_name = 'handle_{}'.format(cmd)

            if random.random() < 0.1:
                spawn(phrases.handle, self, message, 'phrase', args)
            else:
                for handler in self.handlers:
                    if hasattr(handler, method_name):
                        spawn(handler.handle, self, message, cmd, args)
                        break
        else:
            for handler in self.handlers:
                if hasattr(handler, 'handle_message'):
                    if handler.handle_message(self, message):
                        break

    def loop(self):
        while not self.terminated:
            try:
                if not self.initial:
                    updates = self.telegram.getUpdates(timeout=5, offset=self.id)
                else:
                    updates = self.telegram.getUpdates(timeout=0, offset=self.id)
                for update in updates:
                    if not self.initial:
                        self.handle_update(update)
                    self.id = max(self.id, update.update_id + 1)
                self.initial = False
            except KeyboardInterrupt:
                self.terminated = True
                print('Bye!')
            except:
                traceback.print_exc()

    def stop(self):
        self.terminated = True


if __name__ == '__main__':
    bot = Bot()
    try:
        assert int(os.environ['NO_STATS']) == 1
        print('Stats disabled')
    except (KeyError, ValueError, TypeError, AssertionError) as e:
        bot.add_handlers(handlers.Stats())
    try:
        assert int(os.environ['NO_VK']) == 1
        print('VK auth disabled')
    except (KeyError, ValueError, TypeError, AssertionError) as e:
        bot.add_handlers(handlers.VKAudioHandler())

    bot.add_handlers(
        handlers.GenericHandler(),
        # handlers.GoogleHandler(),
        handlers.FooHandler(), handlers.Pasta(), handlers.Fortune(),
        handlers.DotaRandom(), handlers.Roll(), handlers.Questions(), handlers.Facts(), handlers.PornRoll(),
        handlers.Stars(), handlers.BarrelRollHandler(), handlers.AdminHandler(),
        handlers.TitsBoobsHandler(), handlers.ResponseHandler(), handlers.UTHandler(),
        handlers.RealGirlsHandler(), handlers.CancelHandler()
    )

    # tasks.NineGagPoster(bot)
    tasks.YouTubeWatcher(bot)

    bot.loop()
