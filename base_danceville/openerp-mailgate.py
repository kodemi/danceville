#!/usr/bin/python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################



import email, imaplib
import xmlrpclib
import datetime
import re
import logging

MAIL_SERVER = 'imap.gmail.com'
MAIL_PORT = '993'
MAIL_LOGIN = 'danceville.russia@gmail.com'
MAIL_PASSWORD = 'danceville111'
NEW_REQUEST_MAILBOX = 'new_requests'
FINISHED_REQUEST_MAILBOX = 'finished_requests'
FAILED_REQUEST_MAILBOX = 'failed_requests'
PARTNER_CATEGORY = u'dw_w11'
PARTNER_CATEGORY2 = u'unpaid'

class rpc_proxy(object):
    def __init__(self, uid, passwd, host='localhost', port=8069, path='object', dbname='terp'):
        self.rpc = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/%s' % (host, port, path))
        self.user_id = uid
        self.passwd = passwd
        self.dbname = dbname

    def __call__(self, *request):
        return self.rpc.execute(self.dbname, self.user_id, self.passwd, *request)

def parse_email(msg, options):
    rpc = rpc_proxy(options.userid, options.password, host=options.host, dbname=options.dbname)
    #try:
    #    section_id = int(options.section)
    #except:
    #    section_id = rpc('crm.case.section', 'search', [('code','=',options.section)])[0]
    #email = options.email
    message = msg.get_payload(None, True)
    if not message:
        logger.error("Invalid request")
        return False, '???' 
    message = message.split('\n')
    partner = {}
    for line in message:
        tmp = line.split(':')
        if tmp[0].strip() not in ['surname', 'firstname', 'middlename',
                                  'dance_collective', 'city', 'country',
                                  'language', 'birthday', 'email',
                                  'mobile', 'vkontakte_id', 'facebook_id',
                                  'card', '\n', '']:
            logger.error("Invalid request")
            return False, '???' 
	if len(tmp) == 2:
            partner[tmp[0].strip()] = tmp[1].strip()
        elif len(tmp) == 3:
            try:
                name = ' '.join([partner['surname'], partner['firstname'], partner['middlename']])
            except Exception:
                name = '???'
            fieldname = tmp[0].strip()
            logger.warning("Invalid field: %s -> %s (%s)" % (fieldname, ''.join(tmp[1:]).strip(), name))
            try:
                value = re.findall(r'.*/(.*)$', ''.join(tmp[1:]))[0]  # parse vkontakte_id
            except Exception:
                value = False 
            if not value:
                logger.error("Can't parse field: %s (%s)" % (fieldname, name))
                return False, name
            else:
                partner[fieldname] = value 
    if not partner:
        return False, False
    category_id = rpc('res.partner.category', 'search', [('name', '=', PARTNER_CATEGORY)])
    category_child_id = rpc('res.partner.category', 'search', [('name', '=', PARTNER_CATEGORY2), 
                                                               ('parent_id', '=', category_id[0])])
    for field in ['surname', 'firstname', 'middlename']:
        partner[field] = partner[field].replace('ё','е').replace('Ё', 'Е').decode('utf8').capitalize()
    name = ' '.join([partner['surname'], partner['firstname'], partner['middlename']])
    birthday = partner['birthday'].split('.')
    if len(birthday) != 3:
        birthday = partner['birthday'].split('-')
        if len(birthday) != 3:
            birthday = partner['birthday'].split('/')
            if len(birthday) != 3:
                birthday = partner['birthday'].split(',')
                if len(birthday) != 3:
                    birthday = partner['birthday'].split(' ')
                    if len(birthday) != 3:
                        logger.error("Invalid field: %s -> %s (%s)" % ('birthday', 
                                                     partner['birthday'], name))
                        return False, name
    if birthday:
        if len(birthday[2]) == 2:
            birthday[2] = "19%s" % birthday[2]    
        if len(birthday[0]) == 1:
            birthday[0] = "0%s" % birthday[0]
        if len(birthday[1]) == 1:
            birthday[1] = "0%s" % birthday[1]
        birthday = "%s-%s-%s" % (birthday[2], birthday[1], birthday[0])
    partner['birthday'] = birthday
    exist_id = rpc('res.partner', 'search', [('name', '=', name)])
    update = False
    if exist_id:
        check_identic = []
        for id in exist_id:
            exist_birthday = rpc('res.partner', 'read', id, ['birthday'])['birthday']
            if exist_birthday == birthday:
                check_identic.append(id)
        if len(check_identic) != 1:
            logger.error("Can't select existing partner to update (%s)" % name)
            return False, name 
        exist_id = check_identic[0]
        update = True 
    if update:
        exist_partner = rpc('res.partner', 'read', exist_id)
        #logger.debug("%s, %s" % (category_id, exist_partner['category_id']))
        #if category_id[0] not in exist_partner['category_id']:
        category_id.extend(exist_partner['category_id'])
    partner['category_id'] = [[6, 0, category_id + category_child_id]]
    # correction of field name
    partner['lang'] = partner.pop('language')
    if 'русский' in partner['lang'] or 'Русский' in partner['lang']:
        partner['lang'] = 'ru_RU'
    else:
        partner['lang'] = 'en_US'
    # correction of field name
    partner['country_id'] = partner.pop('country')
    if partner['country_id'] in ['РФ', 'Р.Ф.', '-']:
        partner['country_id'] = 'Россия'
    country_trans_id = rpc('ir.translation', 'search', [('value', '=', partner['country_id'])])
    if not country_trans_id:
        logger.error("Invalid field: %s -> %s (%s)" % ('country', 
                                        partner['country_id'].decode('utf-8'), name))
        country_trans_id = rpc('ir.translation', 'search', [('value', '=', 'Россия')])
    partner['country_id'] = rpc('ir.translation', 'read', country_trans_id)[0]['res_id']
    partner['danceville_card_type_id'] = rpc('danceville.cards', 'search', [('name', '=', partner['card'])])[0]
    partner.pop('card')
    for i in ['facebook_id', 'vkontakte_id']:
        if partner[i] in ['отсутствует','Отсутствует', 'нет', 'Нет', '-', '0']:
            partner[i] = False 
    partner['mobile'] = partner['mobile'].replace('(','').replace(')','').replace('-','').replace(' ','')
    partner_address = {}
    # partner.address fields
    for field in ('country_id', 'city', 'mobile', 'email', 'vkontakte_id', 'facebook_id'):
        partner_address[field] = partner.pop(field)
    partner_address['type'] = 'default'
    partner['address'] = [(0, 0, partner_address)]  
    id = False
    try:
        if not update: 
            id = rpc('res.partner', 'create', partner) 
        else:
            addr = partner.pop('address')[0][2]
            rpc('res.partner', 'write', exist_id, partner)
            addr_id = rpc('res.partner.address', 'search', [('partner_id', '=', exist_id)])
            id = rpc('res.partner.address', 'write', addr_id, addr)
    except Exception,e:
        if getattr(e,'faultCode','') and 'AccessError' in e.faultCode:
            e = 'The Specified user does not have an access to the CRM case.'
        logger.error(e)
    return id, name   


if __name__ == '__main__':
    import sys, optparse
    parser = optparse.OptionParser(
        usage='usage: %prog [options]',
        version='%prog v1.0')

    group = optparse.OptionGroup(parser, "Note",
        "This program parse a mail from standard input and communicate "
        "with the Open ERP server for case management in the CRM module.")
    parser.add_option_group(group)

    parser.add_option("-u", "--user", dest="userid", help="ID of the user in Open ERP", default=1, type='int')
    parser.add_option("-p", "--password", dest="password", help="Password of the user in Open ERP", default='admin')
    parser.add_option("-d", "--dbname", dest="dbname", help="Database name (default: terp)", default='terp')
    parser.add_option("--host", dest="host", help="Hostname of the Open ERP Server", default="localhost")
    #parser.add_option("-l", dest="logfile", help="Name of the log file", default="/var/log/openerp-mailgate.log")

    (options, args) = parser.parse_args()

    logger = logging.getLogger('mailgate')
    logger.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    
    box = imaplib.IMAP4_SSL(MAIL_SERVER,MAIL_PORT)
    box.login(MAIL_LOGIN, MAIL_PASSWORD)
    box.select(NEW_REQUEST_MAILBOX)
    typ, [msg_ids] = box.search(None, 'ALL')
    msg_ids = ','.join(msg_ids.split(' '))
    failed = []
    finished_msg_ids = []
    failed_msg_ids = []
    for msg_id in msg_ids.split(','):
        if not msg_id:
            continue
        typ, data = box.fetch(msg_id, '(RFC822)')
        msg_txt = email.message_from_string(data[0][1])
        response, name = parse_email(msg_txt, options)
        if not response:
            logger.error("Request failed (%s)" % name)
            failed.append(name)
        elif response is True:
            logger.info("Request sucessfully processed. Partner updated (%s)" % name) 
        else:
            logger.info("Request sucessfully processed. Partner added (%s)" % name) 
        if not response:
            failed_msg_ids.append(msg_id)
        else:
            finished_msg_ids.append(msg_id)
    failed_msg_ids = ','.join(failed_msg_ids)
    finished_msg_ids = ','.join(finished_msg_ids)
    if finished_msg_ids:
        box.copy(finished_msg_ids, FINISHED_REQUEST_MAILBOX)
    #    typ, response = box.store(finished_msg_ids, '+FLAGS', r'(\Deleted)')
    if failed_msg_ids:
        box.copy(failed_msg_ids, FAILED_REQUEST_MAILBOX)
    #    typ, response = box.store(failed_msg_ids, '+FLAGS', r'(\Deleted)')
    if msg_ids:
        typ, response = box.store(msg_ids, '+FLAGS', r'(\Deleted)')
        typ, response = box.expunge()
    box.close() 
    box.logout()
    if failed:
        logger.info("Requests with errors: %s" % ', '.join(failed))
