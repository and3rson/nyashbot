# coding: utf-8

from __future__ import print_function

import sqlite3
import json


class DB(object):
    def __init__(self, filename='./db.sqlite'):
        self.conn = sqlite3.connect(filename, isolation_level=None)

    def upsert(self, name, columns):
        table = self.select('SELECT name FROM sqlite_master WHERE type="table" AND name="{}"'.format(name))
        if not table:
            self.execute('CREATE TABLE {} (id integer primary key autoincrement not null, {})'.format(
                name,
                ', '.join([
                    '{} {}'.format(column[0], column[1])
                    for column
                    in columns
                ])
            ))

    def execute(self, query, args=()):
        cursor = self.conn.cursor()
        cursor.execute(query, args)
        return cursor

    def select(self, query, args=()):
        return self.execute(query, args).fetchall()


db = DB('./db.sqlite')
stars = DB('./stars.sqlite')


def get_var(key, default=None):
    try:
        f = open('vars.db', 'r')
        data = json.loads(f.read())
        f.close()
    except IOError:
        f = open('vars.db', 'w')
        f.write('{}')
        f.close()
        data = dict()

    return data.get(key, default)


def set_var(key, value):
    try:
        f = open('vars.db', 'r')
        data = json.loads(f.read())
        f.close()
    except IOError:
        f = open('vars.db', 'w')
        f.write('{}')
        f.close()
        data = dict()

    data[key] = value

    f = open('vars.db', 'w')
    f.write(json.dumps(data))
    f.close()
