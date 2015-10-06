# coding: utf-8

from __future__ import print_function

import sqlite3


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


db = DB()
