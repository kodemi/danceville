# -*- encoding: utf-8 -*-


from osv import fields,osv
import netsvc
import datetime
import hashlib
import logging

logger = netsvc.Logger()

#class payments(osv.osv):
#    _name = 'danceville.payments'
#    _columns = {
#        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='set null', select=True),
#        'payment': fields.integer('Payment'),
#    } 
#payments()

class res_partner_address(osv.osv):
    """
    res_partner_address
    """
    _inherit = 'res.partner.address'

    def _compose_name(self, cr, uid, ids, field_name, arg, context):
        address = self.browse(cr, uid, ids[0], context=context)
        partner = self.pool.get("res.partner")
        partner_id = partner.search(cr, uid, [('id', '=', address.partner_id.id)]) 
        if not partner_id:
            return False
        partner_id = partner_id[0]
        partner_name = partner.browse(cr, uid, partner_id).name
        result = { ids[0]: partner_name }
        return result

    _columns = {
        'name': fields.function(
            _compose_name,
            type='char',
            size=64,
            method=True,
            store=True,
            string='Name',
            readonly=False),
        'vkontakte_id': fields.char('VKontakte ID', size=64),
        'facebook_id': fields.char('Facebook ID', size=64),
    }
    _defaults = {
        'type': lambda *a: 'default',
    }
res_partner_address()


class res_partner(osv.osv):

    def unlink(self, cr, uid, ids, context=None):
        address = self.pool.get('res.partner.address')
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        for id in ids:
            partner = self.browse(cr, uid, id, context=context)
            addrs_ids = address.search(cr, uid, [('partner_id', '=', id)]) 
            for addr_id in addrs_ids:
                 address.unlink(cr, uid, addr_id)  
        return super(res_partner, self).unlink(cr, uid, ids, context)

    def _compose_name(self, cr, uid, ids, field_name, arg, context):
        result = {}
        for id in ids:
            partner = self.browse(cr, uid, id, context=context)
            """
            joinlist = []
            partnername = (partner.surname, partner.firstname, partner.middlename)
            for part in partnername:
                if part:
                    joinlist.append(part.strip())
            name = ' '.join(joinlist)
            if not name:
                name = partner.name   
            """
            name = ' '.join(partner.name.split())
            result[id] = name
        return result

    def _calculate_age(self, cr, uid, ids, field_name, arg, context):
        result = {}
        for id in ids:
            partner = self.browse(cr, uid, id, context=context)
            if partner.birthday:
                birthday = datetime.datetime.strptime(partner.birthday, '%Y-%m-%d')
                age = (datetime.datetime.today() - birthday).days / 365
            else:
                age = 0
            result[id] = age
        return result 
    
    def write(self, cr, uid, ids, vals, context=None):
        if 'name' in vals:
            vals['name'] = u' '.join([part.capitalize() for part in vals['name'].decode('utf-8').split()])
        return super(res_partner, self).write(cr, uid, ids, vals, context=context)

    def hash(self, cr, uid, name, email, context=None):
        hash_str = u"{0} {1}".format(name, email).encode('utf-8')
        return hashlib.sha1(hash_str).hexdigest()

    def calculate_hash(self, cr, uid, ids, context=None):
        partners = self.browse(cr, uid, ids, context=context)
        result = []
        for partner in partners:
            email = partner.email
            name = partner.name
            result.append((partner.id, self.hash(cr, uid, name, email)))
        return result

    def _calculate_hash(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for id in ids:
            result[id] = self.calculate_hash(cr, uid, [id], context)[0][1]
        return result

    def unsubscribe(self, cr, uid, ids, context=None):
        if not hasattr(ids, '__iter__'):
            ids = [ids]
        for partner_id in ids:
            partner_obj = self.browse(cr, uid, partner_id)
            if not partner_obj.category_id:
                self.unlink(cr, uid, partner_id)
            else:
                self.write(cr, uid, ids, {'is_subscriber': False})
        return True

    _name = 'res.partner'
    _inherit = 'res.partner'
    _columns = {
        #'firstname': fields.char('First name', size=64, required=False),
        #'surname': fields.char('Surname', size=64, required=False),        
        #'patronymic': fields.char('Patronymic', size=64, required=False),
        'is_trainer': fields.boolean('Trainer'),
        'is_head_of_school': fields.boolean('Head of School'),
        'is_dance_project': fields.boolean('Dance project'),
        'dance_style': fields.char('Dance style', size=64),
        'dance_collective': fields.char('Collective', size=64),
        'birthday': fields.date('Birthday'),
        'age': fields.function(
            _calculate_age,
            type='integer',
            method=True,
            store=True,
            string='Age',
            select=2),
        'hash': fields.function(
            _calculate_hash,
            type='char',
            size=40,
            method=True,
            store=True),
        'is_subscriber': fields.boolean('Subscribe to mails'),
    }
    _defaults = {
        'is_subscriber': lambda *a: True,
    }
res_partner()
