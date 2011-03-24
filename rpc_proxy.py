#!/usr/bin/python
# -*- encoding: utf-8 -*-

import xmlrpclib

class rpc_proxy(object):
    def __init__(self, uid, passwd, host='localhost', port=8069, path='object', dbname='terp'):
        self.rpc = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/%s' % (host, port, path))
        self.user_id = uid
        self.passwd = passwd
        self.dbname = dbname

    def __call__(self, *request):
        return self.rpc.execute(self.dbname, self.user_id, self.passwd, *request)

#rpc = rpc_proxy(1,'URcfhhu5',host='danceville.dyndns-office.com',dbname='danceville')

