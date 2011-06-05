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
import imap4utf7
from email.header import decode_header


MAIL_SERVER = 'imap.gmail.com'
MAIL_PORT = '993'
MAIL_LOGIN = 'registration@danceville.ru'
MAIL_PASSWORD = '44G5P4g1'
NEW_REQUEST_MAILBOX = 'test1' #'new_requests'
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

def parse_email(msg, msg_type, rpc):
    message = msg.get_payload(None, True)
    if not message:
        logger.error("Invalid request")
        return False, '???'
    message = message.split('\n')
    if msg_type == u'Регистрация':
        id, name = create_lead(message, rpc)
        return id, name
    elif msg_type == u'Заявка':
        id, name = create_opportunity(message, rpc)
        return id, name
    elif msg_type == u'Предоплата':
        create_prepaid(message, rpc)
        return False, '???'
    else:
        return False, '???'
    
def create_lead(message, rpc):
    lead = {}
    for line in message:
        tmp = line.split(':')
        if tmp[0].strip() not in ['surname', 'firstname', 'middlename',
                                  'dance_collective', 'city', 'country',
                                  'language', 'birthday', 'email',
                                  'mobile', 'vkontakte_id', 'facebook_id',
                                  '\n', '']:
            logger.error("Invalid request")
            return False, '???'
        if len(tmp) == 2:
            lead[tmp[0].strip()] = tmp[1].strip()
        elif len(tmp) == 3:
            try:
                name = ' '.join([lead['surname'], lead['firstname'], lead['middlename']])
            except Exception:
                name = '???'
            fieldname = tmp[0].strip()
            logger.warning("Invalid field: %s -> %s (%s)" % (fieldname, ''.join(tmp[1:]).strip(), name))
            try:
                value = re.findall(r'\w+', ''.join(tmp[1:]))[-1]  # parse vkontakte_id
            except Exception:
                value = False
            if not value:
                logger.error("Can't parse field: %s (%s)" % (fieldname, name))
                return False, name
            else:
                lead[fieldname] = value
    if not lead:
        return False, '???'
    lead['partner_name'] = ' '.join([lead.pop('surname'), lead.pop('firstname'), lead.pop('middlename')])
    lead['name'] = '[Регистрация] %s' % lead['partner_name']
    lead['country_id'] = lead.pop('country')
    lead['email_from'] = lead.pop('email')
    for i in ['facebook_id', 'vkontakte_id']:
        if lead[i] in ['отсутствует','Отсутствует', 'нет', 'Нет', '-', '0']:
            lead[i] = False
    id = False
    try:
        id = rpc('crm.lead', 'create_from_web', lead)
    except Exception,e:
        if getattr(e,'faultCode','') and 'AccessError' in e.faultCode:
            e = 'The Specified user does not have an access to the CRM case.'
        logger.error(e)
    return id, lead['name']

def create_opportunity(message, rpc):
    partner = {}
    for line in message:
        tmp = line.split(':')
        if tmp[0].strip() not in ['surname', 'firstname', 'middlename',
                                  'email', 'card', '\n', '']:
            logger.error("Invalid request")
            return False, '???'
        if len(tmp) == 2:
            partner[tmp[0].strip()] = tmp[1].strip()
        elif len(tmp) == 3:
            try:
                name = ' '.join([lead['surname'], lead['firstname'], lead['middlename']])
            except Exception:
                name = '???'
            fieldname = tmp[0].strip()
            logger.warning("Invalid field: %s -> %s (%s)" % (fieldname, ''.join(tmp[1:]).strip(), name))
    if not partner:
        return False, '???'
    for field in ['surname', 'firstname', 'middlename']:
        partner[field] = partner[field].replace('ё','е').replace('Ё', 'Е').decode('utf8').capitalize()
    partner['name'] = ' '.join([partner.pop('surname'), partner.pop('firstname'), partner.pop('middlename')])
    #partner_hash = rpc('res.partner', 'hash', partner['name'], partner['email'])
    #partner_id = rpc('res.partner', 'search', [('hash', '=', partner_hash)])
    #partner_id = partner_id and partner_id[0]
    lead_id = rpc('crm.lead', 'search', [('partner_name', '=', partner['name']), ('email_from', 'ilike', partner['email'])])
    if lead_id:
        opp_id = rpc('crm.lead', 'lead2opportunity', lead_id, partner['card'])
        return opp_id, partner['name']
    else:
        return False, partner['name']

def create_prepaid(message, rpc):
    partner = {}
    for line in message:
        tmp = line.split(':')
        if tmp[0].strip() not in ['surname', 'firstname', 'middlename',
                                  'email', 'bank', 'payment_number',
                                  'sum', 'date_arrival', 'qr-code_pass_id', '\n', '']:
            logger.error("Invalid request")
            return False, '???'
        if len(tmp) == 2:
            partner[tmp[0].strip()] = tmp[1].strip()
        elif len(tmp) == 3:
            try:
                name = ' '.join([lead['surname'], lead['firstname'], lead['middlename']])
            except Exception:
                name = '???'
            fieldname = tmp[0].strip()
            logger.warning("Invalid field: %s -> %s (%s)" % (fieldname, ''.join(tmp[1:]).strip(), name))
    if not partner:
        return False, '???'
    for field in ['surname', 'firstname', 'middlename']:
        partner[field] = partner[field].replace('ё','е').replace('Ё', 'Е').decode('utf8').capitalize()
    partner['name'] = ' '.join([partner.pop('surname'), partner.pop('firstname'), partner.pop('middlename')])
    return False, '???'

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
    parser.add_option("-d", "--dbname", dest="dbname", help="Database name (default: terp)", default='test')
    parser.add_option("--host", dest="host", help="Hostname of the Open ERP Server", default="localhost")
    #parser.add_option("-l", dest="logfile", help="Name of the log file", default="/var/log/openerp-mailgate.log")

    (options, args) = parser.parse_args()
    rpc = rpc_proxy(options.userid, options.password, host=options.host, dbname=options.dbname)

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
    #typ, [msg_ids] = box.search(None, 'ALL')
    finished_msg_ids = []
    failed_msg_ids = []
    failed = []
    all_msg_ids = []
    for msg_type in (u'Регистрация', u'Заявка', u'Предоплата'):
        logger.info(msg_type)
        typ, [msg_ids] = box.search('utf-8', '(SUBJECT %s)' % msg_type.encode('utf-8'))
        msg_ids = msg_ids.split(' ')
        all_msg_ids.extend(msg_ids)
        for msg_id in msg_ids:
            if not msg_id:
                continue
            typ, data = box.fetch(msg_id, '(RFC822)')
            msg_txt = email.message_from_string(data[0][1])
            response, name = parse_email(msg_txt, msg_type, rpc)
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
        typ, response = box.store(','.join(all_msg_ids), '+FLAGS', r'(\Deleted)')
        typ, response = box.expunge()
    box.close()
    box.logout()
    if failed:
        logger.info("Requests with errors: %s" % ', '.join(failed))
