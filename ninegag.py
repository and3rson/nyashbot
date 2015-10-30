#!/usr/bin/env python2

import urllib2
from bs4 import BeautifulSoup


class NineGag(object):
    class Article(object):
        def __init__(self, doc):
            self.id = doc['data-entry-id']
            self.url = doc['data-entry-url']
            self.name = doc.find('header').find('a').text.strip()
            self.content_doc = doc.find('div', class_='post-container')
            self.animated = self.content_doc.find('div', class_='badge-animated-container-animated')
            self.img = self.content_doc.find('img', class_='badge-item-img')
            self.read_more = self.content_doc.find('a', class_='post-read-more')
            if self.animated:
                self.kind = 'gif'
            elif self.read_more:
                self.kind = 'article'
            elif self.img:
                self.kind = 'image'
            else:
                self.kind = 'unknown'

        def __str__(self):
            return '<9gag:Entry id={} kind={} "{}">'.format(self.id, self.kind, self.name)

        def __unicode__(self):
            return self.__str__()

        def __repr__(self):
            return self.__str__()

    BASE_URL = 'http://9gag.com'

    def __init__(self):
        pass

    def get_latest_hot(self):
        doc = self.get('/hot')
        article_doc_list = doc.find_all('article')
        return [
            NineGag.Article(article_doc)
            for article_doc
            in article_doc_list
        ]

    def get(self, url):
        opener = urllib2.build_opener()
        opener.addheaders.append(('Cookie', 'safemode=0'))
        response = opener.open(NineGag.BASE_URL + url)
        return BeautifulSoup(response.read(), 'lxml')
