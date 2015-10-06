#!/usr/bin/env python2.7
# coding: utf-8

from __future__ import print_function

import sys
import telegram
import re
import handlers

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
        self.bot = telegram.Bot(token=settings.TOKEN)
        self.initial = True
        self.id = 0
        self.handlers = []

    def add_handlers(self, *args):
        for handler in args:
            self.handlers.append(handler)

    def handle_update(self, update):
        message = update.message
        match = re.findall('^/([a-zA-Z_0-9]+)(\s+(.+$))?', message.text.strip())
        try:
            if match:
                match = match[0]
                cmd = match[0].lower()
                args = match[2]
                for handler in self.handlers:
                    if handler.handle(self.bot, message, cmd, args):
                        break
            else:
                for handler in self.handlers:
                    if handler.handle_message(self.bot, message):
                        break
        except Exception as e:
            self.bot.sendMessage(
                chat_id=message.chat_id,
                text='**{}**: {}'.format(str(e.__class__.__name__), str(e)),
                parse_mode='Markdown'
            )

    def loop(self):
        while True:
            if not self.initial:
                updates = self.bot.getUpdates(timeout=5, offset=self.id)
            else:
                updates = self.bot.getUpdates(timeout=0, offset=self.id)
            for update in updates:
                if not self.initial:
                    self.handle_update(update)
                self.id = max(self.id, update.update_id + 1)
            self.initial = False

bot = Bot()
bot.add_handlers(
    handlers.Stats(), handlers.GoogleHandler(), handlers.FooHandler(), handlers.Pasta(), handlers.Fortune()
)
bot.loop()
