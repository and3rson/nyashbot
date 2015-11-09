import traceback
from gevent import Greenlet
from ninegag import NineGag
from youtube import YouTube
from db import db, get_var, set_var
import configurator


class Task(object):
    def __init__(self, engine):
        self.engine = engine

    def run(self):
        raise NotImplementedError

    def start_later(self, seconds):
        Greenlet(self.run).start_later(seconds)


class NineGagPoster(Task):
    def __init__(self, engine):
        super(NineGagPoster, self).__init__(engine)

        db.upsert('gags', [
            ('gag', 'varchar(16)'),
            ('kind', 'varchar(16)'),
            ('date_added', 'timestamp default current_timestamp'),
        ])

        self.ng = NineGag()
        self.start_later(1)

    def run(self):
        try:
            gags = self.ng.get_latest_hot()[::-1]
            for gag in gags:
                match = db.select('SELECT * FROM gags WHERE gag="{}"'.format(gag.id))
                if not match:
                    # New gag!
                    db.execute('INSERT INTO gags(gag, kind) VALUES("{}", "{}")'.format(gag.id, gag.kind))

                    if gag.kind == 'image':
                        self.engine.telegram.sendPhoto(
                            chat_id=configurator.get('CHAT_ID'),
                            photo=gag.img['src'],
                            caption=gag.name
                        )
                    elif gag.kind == 'gif':
                        import urllib2
                        from random import random
                        data = urllib2.urlopen(gag.animated['data-mp4']).read()
                        tmp = open('/tmp/{}.mp4'.format(str(int(random() * 1000000))), 'w+b')
                        tmp.write(data)
                        tmp.seek(0)

                        self.engine.telegram.sendVideo(
                            chat_id=configurator.get('CHAT_ID'),
                            video=tmp,
                            caption=gag.name
                        )
                    elif gag.kind == 'article':
                        self.engine.telegram.sendPhoto(
                            chat_id=configurator.get('CHAT_ID'),
                            photo=gag.img['href'],
                            caption=u'Full version: {}'.format(gag.name)
                        )
            # print 'NineGagPoster.run()'
            self.start_later(3)
        except:
            traceback.print_exc()
            self.start_later(60)


class YouTubeWatcher(Task):
    def __init__(self, engine):
        super(YouTubeWatcher, self).__init__(engine)

        # db.upsert('youtube', [
        #     ('channel', 'varchar(64)'),
        #     ('video_id', 'varchar(64)')
        # ])

        self.yt = YouTube()
        self.start_later(1)

    def run(self):
        channels = ('DotaCinema', 'WronchiAnimation')

        for channel in channels:
            try:
                videos = self.yt.get_latest(channel)
                video = videos[0]

                last_video_id = get_var('youtube.{}.last_id'.format(channel), '')
                if video.id != last_video_id:
                    set_var('youtube.{}.last_id'.format(channel), video.id)
                    print 'New video: {}'.format(str(video))

                    self.engine.telegram.sendPhoto(
                        chat_id=configurator.get('CHAT_ID'),
                        photo=video.img,
                        caption=u'{}: {}'.format(video.name, video.url)
                    )

                # match = db.select('SELECT * FROM youtube WHERE id="{}"'.format(video.id))
            except:
                traceback.print_exc()

        self.start_later(60)
