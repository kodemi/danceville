#!/usr/bin/env python

from rpc_proxy import rpc_proxy
import cPickle as pickle

rrpc = rpc_proxy(1,'URcfhhu5',host='danceville.dyndns-office.com',dbname='danceville')
#lrpc = rpc_proxy(1,'admin',host='localhost',dbname='danceville')

rpartners_ids = rrpc('res.partner', 'search', [])
for rpid in rpartners_ids[1:]:
    rpartner = rrpc('res.partner', 'read', rpid, [])
    del rpartner['surname'], rpartner['middlename'], rpartner['firstname'], rpartner['events'], rpartner['id']
    #print rpartner.keys()
    #lpartner = lrpc('res.partner', 'read', 1, [])
    #print lpartner.keys()
    if rpartner['address']:
        raddress = rrpc('res.partner.address', 'read', rpartner['address'][0], [])
        del raddress['id'], raddress['partner_id']
    else:
        raddress = {}
    #laddress = lrpc('res.partner.address', 'read', 1, [])
    #print laddress
    lpartner = rpartner
    #lpartner = {'name': 'test'}
    lpartner['address'] = [(0, 0, raddress)]
    category = rrpc('res.partner.category', 'read', rpartner['category_id']) 
    lpartner['category_id'] = category  
    #print lpartner
    #lrpc('res.partner', 'create', lpartner)
    #break
    pickle.dump(lpartner, open("partners", "ab"))
