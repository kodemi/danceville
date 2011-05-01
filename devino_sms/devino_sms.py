#-*- cofing: utf-8 -*-

from osv import fields, osv
import netsvc
import logging
from devino_sms_client import *
from tools.translate import _
logger = netsvc.Logger()

class SMSClient(osv.osv):
    _name = 'sms.smsclient'
    _description = 'SMS Client'
    _inherit = 'sms.smsclient'
    
    _columns = {
        'sender' : fields.char('Mobile No', size=256, required=True)
    }
    
    def send_message(self, cr, uid, gateway, to, from_, text):
        gate = self.browse(cr, uid, gateway)
        
        if not self.check_permissions(cr, uid, gateway):
            raise osv.except_osv(_('Permission Error!'), _('You have no permission to access %s ') % (gate.name,) )
        
        #url = gate.url
        #prms = {}
                        
        #params = urllib.urlencode(prms)
        #req = to
        queue = self.pool.get('sms.smsclient.queue')
        queue.create(cr, uid, {
                    'name': '-'.join([from_, to]), 
                    'gateway_id':gateway,
                    'state': 'draft',
                    'sender': from_,
                    'mobile':to,
                    'msg':text,
                    #'params': params,
                    
                })
        return True
        
    def _check_queue(self, cr, uid, ids=False, context={}):
	#logging.info('%s, %s' % (ids, context))
        queue = self.pool.get('sms.smsclient.queue')
        history = self.pool.get('sms.smsclient.history')
        gate = self.pool.get('sms.smsclient')
        #queue_ = queue.browse(cr, uid, ids[0])
        gate_id = 1#queue_.gateway_id
        url = gate.browse(cr, uid, gate_id).url
	property_ids = gate.browse(cr, uid, gate_id).property_ids
        #params = urlparse.parse_qs(queue_.params)
	props = {}
        for p in property_ids:
            if p.type == 'user':
                props['user'] = p.value
            elif p.type == 'password':
                props['password'] = p.value
        try:
            client = DevinoSmsClient(props['user'], props['password'])
        except DevinoSmsClientException as e:
            logger.notifyChannel(_("Devino.sms"), netsvc.LOG_ERROR, str(e))
            return False
        sids = queue.search(cr, uid, [('state','!=','send'),('state','!=','sending')], limit=30)
        queue.write(cr, uid, sids, {'state':'sending'})
        errors = []
        sent = []
        for sms in queue.browse(cr, uid, sids):
            try:
                res = client.SendMessage(sms.sender, sms.mobile, sms.msg)
                logger.notifyChannel(_("Devino.sms"), netsvc.LOG_INFO, "SMS to %s sent" % sms.mobile)
            except DevinoSmsClientException as e:
                logger.notifyChannel(_("Devino.sms"), netsvc.LOG_ERROR, str(e))
                errors.append((sms.id, str(e)))
                continue
            #f = urllib.urlopen(sms.name)
            #if len(sms.msg) > 160:
            #    error.append(sms.id)
            #    continue
            
            history.create(cr, uid, {
                        'name':'SMS Sent',
                        'gateway_id':sms.gateway_id.id,
                        'sms': sms.msg,
                        'to':sms.mobile,
                        'sender':sms.sender,
                    })
            sent.append(sms.id)
            
        queue.write(cr, uid, sent, {'state':'send'})
	for error in errors:
            queue.write(cr, uid, error[0], {'state':'error', 'error':error[1]})
        return True
SMSClient()

class SMSQueue(osv.osv):
    _name = 'sms.smsclient.queue'
    _description = 'SMS Queue'
    _inherit = 'sms.smsclient.queue'
    _columns = {
        'sender': fields.char('Sender Name', size=64),
    }
SMSQueue()

class Properties(osv.osv):
    _name = 'sms.smsclient.parms'
    _description = 'SMS Client Properties'
    _inherit = 'sms.smsclient.parms'
    _columns = {
        #'user': fields.char('User', size=64),
        #'password': fields.char('Password', size=64),
        'type':fields.selection([
            ('user','User'),
            ('password','Password'),
            ('sender','Sender Name'),
            ('to','Recipient No'),
            ('from','Sender No'),
            ('sms','SMS Message')
        ],'API Method', select=True),
    }
Properties()

class HistoryLine(osv.osv):
    _name = 'sms.smsclient.history'
    _description = 'SMS Client History'
    _inherit = 'sms.smsclient.history'
    _columns = {
        'sender': fields.char('Sender Name', size=64),
    }
HistoryLine()
