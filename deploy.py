#!/usr/bin/env python2.7

import os
import sys
from time import sleep
from subprocess import Popen, PIPE
from datetime import datetime

DIR = '/var/www/anderson/data/src/nyashbot'
LOGFILE = 'log/deploy.log'


def log(s):
    time = datetime.strftime(datetime.now(), format='%d-%m-%Y %H:%M:%S')
    s = s.replace('\n', '\n' + ' ' * (len(time) + 2)).strip()
    f = open(LOGFILE, 'a+')
    f.write('{}: {}\n'.format(time, s))
    f.close()

def log_cmd(*args):
    out, err = call(*args)
    log('Running "{}"\nSTDOUT: {}\nSTDERR: {}'.format(str(args), out, err))

def call(cmd, *args):
    return Popen([cmd] + list(args), stdout=PIPE, stderr=PIPE).communicate()

def deploy():
    os.chdir(DIR)

    sys.path.append(DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "westrampage.settings.production")
    from django.conf import settings

    log_cmd('git', 'stash')
    log_cmd('git', 'stash', 'drop')
    log_cmd('app', 'start', 'westrampage')
    log_cmd('./prod', './manage.py', 'collectstatic', '--noinput')
    log_cmd('wget', '-qO-', 'westrampage.com')
    log_cmd('./prod', './manage.py', 'collectstatic', '--noinput')


if __name__ == '__main__':
    deploy()
