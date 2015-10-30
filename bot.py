#!/usr/bin/env python2.7
# coding: utf-8

from __future__ import print_function

from gevent import spawn, monkey, joinall

monkey.patch_socket()
monkey.patch_ssl()

import os
import sys
import telegram
import re
import handlers
import tasks

try:
    import settings
except ImportError:
    sys.stdout.write("Please create settings.py file this code:\n\nTOKEN = '<YOUR_TOKEN>'\n\n")
    sys.exit(1)


class Scheduler(object):
    def __init__(self):
        pass


class Bot(object):
    def __init__(self):
        self.telegram = telegram.Bot(token=settings.TOKEN)
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
        print(message.chat_id)
        if match:
            match = match[0]
            cmd = match[0].lower()
            args = match[2]
            method_name = 'handle_{}'.format(cmd)
            for handler in self.handlers:
                if hasattr(handler, method_name):
                    spawn(handler.handle, self, message, cmd, args)
                    break
        else:
            for handler in self.handlers:
                if hasattr(handler, 'handle_message'):
                    if handler.handle_message(self.telegram, message):
                        break

    def loop(self):
        while not self.terminated:
            if not self.initial:
                updates = self.telegram.getUpdates(timeout=5, offset=self.id)
            else:
                updates = self.telegram.getUpdates(timeout=0, offset=self.id)
            for update in updates:
                if not self.initial:
                    self.handle_update(update)
                self.id = max(self.id, update.update_id + 1)
            self.initial = False

    def stop(self):
        self.terminated = True


bot = Bot()
try:
    assert int(os.environ['NO_STATS']) == 1
    print('Stats disabled')
except (KeyError, ValueError, TypeError, AssertionError) as e:
    bot.add_handlers(handlers.Stats())
bot.add_handlers(
    handlers.GenericHandler(), handlers.GoogleHandler(), handlers.FooHandler(), handlers.Pasta(), handlers.Fortune(),
    handlers.DotaRandom(), handlers.Roll(), handlers.Questions(), handlers.Facts(), handlers.PornRoll(),
    handlers.Stars(), handlers.BarrelRollHandler()
)

tasks.NineGagPoster(bot)

bot.loop()
