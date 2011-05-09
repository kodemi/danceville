# -*- encoding: utf-8 -*-


from osv import fields,osv
import netsvc
import datetime
import logging

logger = netsvc.Logger()

class crm_lead(osv.osv):
    _name = 'crm.lead'
    _inherit = 'crm.lead'
    _columns = {
        'vkontakte_id': fields.char('VKontakte ID', size=64),
        'facebook_id': fields.char('Facebook ID', size=64),
        'dance_collective': fields.char('Dance collective', size=128),
        'birthday': fields.date('Birthday'),
    }
crm_lead()

class crm_lead2partner(osv.osv_memory):
    """ Converts lead to partner """

    _name = 'crm.lead2partner'
    _description = 'Lead to Partner'
    _inherit = 'crm.lead2partner'
    
    def _create_partner(self, cr, uid, ids, context=None):
        """
        This function Creates partner based on action.
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of Lead to Partner's IDs
        @param context: A standard dictionary for contextual values

        @return : Dictionary {}.
        """
        logging.info('my crm2lead')
        if context is None:
            context = {}

        lead_obj = self.pool.get('crm.lead')
        partner_obj = self.pool.get('res.partner')
        contact_obj = self.pool.get('res.partner.address')
        partner_ids = []
        partner_id = False
        contact_id = False
        rec_ids = context and context.get('active_ids', [])

        for data in self.browse(cr, uid, ids, context=context):
            for lead in lead_obj.browse(cr, uid, rec_ids, context=context):
                if data.action == 'create':
                    partner_id = partner_obj.create(cr, uid, {
                        'name': lead.partner_name or lead.contact_name or lead.name,
                        'user_id': lead.user_id.id,
                        'comment': lead.description,
                        'dance_collective': lead.dance_collective,
                        'birthday': lead.birthday,
                    })
                    contact_id = contact_obj.create(cr, uid, {
                        'partner_id': partner_id,
                        'name': lead.contact_name,
                        'phone': lead.phone,
                        'mobile': lead.mobile,
                        'email': lead.email_from,
                        'fax': lead.fax,
                        'title': lead.title and lead.title.id or False,
                        'function': lead.function,
                        'street': lead.street,
                        'street2': lead.street2,
                        'zip': lead.zip,
                        'city': lead.city,
                        'country_id': lead.country_id and lead.country_id.id or False,
                        'state_id': lead.state_id and lead.state_id.id or False,
                        'facebook_id': lead.facebook_id,
                        'vkontakte_id': lead.vkontakte_id,
                    })

                else:
                    if data.partner_id:
                        partner_id = data.partner_id.id
                        contact_id = partner_obj.address_get(cr, uid, [partner_id])['default']
                self.assign_partner(cr, uid, lead.id, partner_id)
                partner_ids.append(partner_id)
        return partner_ids
crm_lead2partner()