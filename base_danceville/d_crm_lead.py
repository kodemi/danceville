# -*- encoding: utf-8 -*-


from osv import fields,osv
import netsvc
import datetime
import re
import logging
import time
from tools.translate import _

logger = netsvc.Logger()

class crm_lead(osv.osv):

    def create_from_web(self, cr, uid, vals, context=None):
        channel_model = self.pool.get('res.partner.canal')
        channel_id = channel_model.search(cr, uid, [('name','=','www.danceville.ru')])
        vals['channel_id'] = channel_id and channel_id[0]
        vals['birthday'] = '-'.join([p for p in vals['birthday'].split('.')[::-1]])
        if vals['country_id'] in [u'Россия', u'РФ', u'Р.Ф.']:
            vals['country_id'] = u'Российская Федерация'
        translation_model = self.pool.get('ir.translation')
        country_transl_id = translation_model.search(cr, uid, [('value', '=', vals['country_id'])])
        vals['country_id'] = country_transl_id and translation_model.read(cr, uid, country_transl_id)[0]['res_id']
        vals['partner_name'] = vals['partner_name'].replace(u'ё',u'е').replace(u'Ё', u'Е')
        vals['contact_name'] = vals['partner_name']
        vals['mobile'] = ''.join(re.split(r'\W+', vals['mobile']))
        vals['state'] = 'open'
        vals['stage_id'] = self.pool.get('crm.case.stage').search(cr, uid, [('name', '=', 'New')])[0]
        return super(crm_lead, self).create(cr, uid, vals, context)

    def _create_partner(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        lead_obj = self.pool.get('crm.lead')
        partner_obj = self.pool.get('res.partner')
        contact_obj = self.pool.get('res.partner.address')
        partner_ids = []
        partner_id = False
        contact_id = False
        #rec_ids = context and context.get('active_ids', [])
        partner_exist = False

        for lead in lead_obj.browse(cr, uid, ids, context=context):
            hash = partner_obj.hash(cr, uid, lead.partner_name, lead.email_from)
            partner_id = partner_obj.search(cr, uid, [('hash', '=', hash)])
            if not partner_id:
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
                partner_id = partner_id[0]
                partner_obj.write(cr, uid, partner_id, {
                    'dance_collective': lead.dance_collective,
                    'birthday': lead.birthday,
                })
                contact_id = partner_obj.address_get(cr, uid, [partner_id])['default']
                contact_obj.write(cr, uid, contact_id, {
                    'mobile': lead.mobile,
                    'email': lead.email_from,
                    'city': lead.city,
                    'country_id': lead.country_id and lead.country_id.id or False,
                    'facebook_id': lead.facebook_id,
                    'vkontakte_id': lead.vkontakte_id,
                })
            self.assign_partner(cr, uid, lead.id, partner_id)
            partner_ids.append(partner_id)
        return partner_ids

    def assign_partner(self, cr, uid, lead_id, partner_id):
        self.pool.get("crm.lead").write(cr, uid, [lead_id], {'partner_id' : partner_id})

    def _convert(self, cr, uid, ids, lead, partner_id, stage_ids, context=None):
        leads = self.pool.get('crm.lead')
        address_id = self.pool.get('res.partner.address').search(cr, uid,
                                                                 [('partner_id', '=', partner_id)],
                                                                 order='create_date desc',
                                                                 limit=1)
        vals = {
            'planned_revenue': lead.planned_revenue,
            'probability': lead.probability,
            'name': lead.name,
            'partner_id': partner_id,
            'user_id': (lead.user_id and lead.user_id.id),
            'type': 'opportunity',
            'stage_id': stage_ids and stage_ids[0] or False,
            'date_action': time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        if address_id:
            vals['partner_address_id'] = address_id[0]

        lead.write(vals, context=context)
        leads.history(cr, uid, [lead], _('Converted to opportunity'), details='Converted to Opportunity', context=context)
        if lead.partner_id:
            msg_ids = [ x.id for x in lead.message_ids]
            self.pool.get('mailgate.message').write(cr, uid, msg_ids, {
                        'partner_id': lead.partner_id.id
                    }, context=context)
            leads.log(cr, uid, lead.id, _("Lead '%s' has been converted to an opportunity.") % lead.name)

    def convert2opportunity(self, cr, uid, ids, context=None):
        leads = self.pool.get('crm.lead')
        converted_leads = []
        for lead in leads.browse(cr, uid, ids, context=context):
            if lead.type == 'opportunity':
                continue
            if(lead.section_id):
                stage_ids = self.pool.get('crm.case.stage').search(cr, uid, [('type','=','opportunity'),('sequence','>=',1), ('section_ids','=', lead.section_id.id)])
            else:
                stage_ids = self.pool.get('crm.case.stage').search(cr, uid, [('type','=','opportunity'),('sequence','>=',1)])
            partner_ids = []
            partner_ids = self._create_partner(cr, uid, ids, context=context)
            partner_id = partner_ids and partner_ids[0] or lead.partner_id.id
            self._convert(cr, uid, ids, lead, partner_id, stage_ids, context=context)
            converted_leads.append(lead.id)
#            if data.name == 'merge':
#                merge_obj = self.pool.get('crm.merge.opportunity')
#                self.write(cr, uid, ids, {'opportunity_ids' : [(6,0, [data.opportunity_ids[0].id])]}, context=context)
#                context.update({'lead_ids' : record_id})
#                return merge_obj.merge(cr, uid, data.opportunity_ids, context=context)
        return converted_leads

    def lead2opportunity(self, cr, uid, ids, card, category=None, context=None):
        converted_leads = self.convert2opportunity(cr, uid, ids)
        opportunity_obj = self.pool.get('crm.lead')
        partner_obj = self.pool.get('res.partner')
        if category:
            category_obj = self.pool.get('res.partner.category')
            category_records = category_obj.name_search(cr, uid, category)
            new_category_id = [category_rec[0] for category_rec in category_records]
        for opp_id in converted_leads:
            opportunity_obj.write(cr, uid, opp_id, {'name': card})
            if category:
                opportunity = opportunity_obj.browse(cr, uid, opp_id)
                partner_id = opportunity.partner_id.id
                category_ids = [category_rec.id for category_rec in partner_obj.browse(cr, uid, partner_id).category_id]
                partner_obj.write(cr, uid, partner_id, {'category_id': [[6, 0, list(set(category_ids) | set(new_category_id))]]})
        return converted_leads


    _name = 'crm.lead'
    _inherit = 'crm.lead'
    _columns = {
        'vkontakte_id': fields.char('VKontakte ID', size=64),
        'facebook_id': fields.char('Facebook ID', size=64),
        'dance_collective': fields.char('Dance collective', size=128),
        'birthday': fields.date('Birthday'),
    }
    _defaults = {
		'optin': lambda *a: True,
	}
crm_lead()
