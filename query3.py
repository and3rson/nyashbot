#!/usr/bin/env python2.7

import socket
import select
import struct
import sys


class Packet(object):
    def __init__(self, data=None):
        self.data = list(data)

    def read(self, n):
        result = self.data[:n]
        del self.data[:n]
        return result

    def readB(self):
        return ord(self.read(1)[0])

    def readW(self):
        return struct.unpack('<H', ''.join(self.read(2)))[0]

    def readD(self):
        return struct.unpack('<I', ''.join(self.read(4)))[0]

    def readS(self):
        length = self.readB()
        return ''.join(self.read(length)[:-1])

    skip = read


class Connection(object):
    def __init__(self, host='dun.ai', port=7778, timeout=5):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.conn.bind(('', 12345))

        self.host = host
        self.port = port
        self.timeout = timeout

    def send(self, data):
        self.conn.sendto(data, (self.host, self.port))

    def recv(self):
        if self.conn in select.select([self.conn], [], [], self.timeout)[0]:
            return Packet(self.conn.recv(1024))
        raise Exception('UT2004 server {}:{} seems to be offline.'.format(self.host, self.port))

    #def send(self, data):
        #self.conn.sendto(data, (HOST, PORT))

    #def recv(self):
        #if self.conn in select.select([self.conn], [], [], TIMEOUT)[0]:
            #data = self.conn.recv(1024)
            #parts = filter(None, data.split('\\'))
            #return dict(zip(parts[::2], parts[1::2]))
        #raise Exception('Timeout while trying to request data.')

    #def request(self, command):
        #self.send('\\{}\\'.format(command))
        #return self.recv()

    def get_info(self):
        self.send('\x7F\x00\x00\x00\x00')
        response = self.recv()

        response.skip(18)

        return dict(
            host=self.host,
            port=self.port,
            server_name=response.readS(),
            map_name=response.readS(),
            game_type=response.readS(),
            player_count=response.readD(),
            max_player_count=response.readD()
        )

#try:
#except Exception as e:
    #print e.message
    #sys.exit(1)
#else:
    #print 'Server: 5.187.7.185:{}'.format(info['hostport'])
    # 'Current map: {}'.format(info['maptitle'])
    #print 'Players: {}/{}'.format(info['numplayers'], info['maxplayers'])
    #print 'Protocol: {}, min: {}'.format(info['gamever'], info['minnetver'])
    #sys.exit(0)
