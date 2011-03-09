#!/usr/bin/env python
#-*- coding: utf-8 -*-

from rpc_proxy import rpc_proxy
import pickle

#rrpc = rpc_proxy(1,'URcfhhu5',host='danceville.dyndns-office.com',dbname='danceville')
lrpc = rpc_proxy(1,'admin',host='localhost',dbname='danceville')
pf = open("partners")
partners = []

try: 
    while True:
        partners.append(pickle.load(pf))
except EOFError:
    pass
print len(partners)
#rpartners_ids = rrpc('res.partner', 'search', [])
for num, partner in enumerate(partners[1:]):
    #rpartner = rrpc('res.partner', 'read', rpid, [])
    #del rpartner['surname'], rpartner['middlename'], rpartner['firstname'], rpartner['events'], rpartner['id']
    #print rpartner.keys()
    #lpartner = lrpc('res.partner', 'read', 1, [])
    #print lpartner.keys()
    #raddress = rrpc('res.partner.address', 'read', rpartner['address'][0], [])
    #del raddress['id'], raddress['partner_id']
    if partner['address'][0][2]:
        if partner['address'][0][2]['country_id']:
            country = partner['address'][0][2]['country_id'][1]
            cid = lrpc('res.country', 'search', [('name','=',country)])[0]
    
    
            partner['address'][0][2]['country_id'] = cid
    #print raddress
        else:
            partner['address'][0][2]['country_id'] = False
    #laddress = lrpc('res.partner.address', 'read', 1, [])
    #print laddress
    lpartner = partner
    #lpartner = {'name': 'test'}
    #lpartner['address'] = [(0, 0, partner['address'])]
    #lpartner['category_id'] = [[6, 0, partner['category_id']]]  
    #print lpartner
    partner['category_id'][0][2] = list(set(partner['category_id'][0][2]))
    print num, partner['name'], partner['category_id']
    lrpc('res.partner', 'create', lpartner)
    #break
