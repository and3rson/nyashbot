#!/usr/bin/env python2

import urllib2
from bs4 import BeautifulSoup


class YouTube(object):
    class Video(object):
        def __init__(self, doc):
            self.url = 'http://www.youtube.com/{}'.format(doc.find('a')['href'].lstrip('/'))
            self.id = self.url.split('=')[-1]
            self.name = doc.find_all('a')[-1]['title']
            self.img = doc.find('img')['src']
            if self.img.startswith('//'):
                self.img = 'http:{}'.format(self.img)

        def __str__(self):
            return '<YT:Video id={} img={}>'.format(self.id, self.img)

        def __unicode__(self):
            return self.__str__()

        def __repr__(self):
            return self.__str__()

    BASE_URL = 'http://youtube.com'

    def __init__(self):
        pass

    def get_latest(self, channel):
        doc = self.get('/user/{}/videos'.format(channel))
        videos_doc_list = doc.find_all('li', class_='channels-content-item')
        return [
            YouTube.Video(article_doc)
            for article_doc
            in videos_doc_list
        ]

    def get(self, url):
        opener = urllib2.build_opener()
        opener.addheaders.append(('Cookie', 'safemode=0'))
        response = opener.open(YouTube.BASE_URL + url)
        return BeautifulSoup(response.read(), 'lxml')
