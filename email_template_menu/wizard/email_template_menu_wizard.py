# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2009 Sharoon Thomas
#    Copyright (C) 2010-2010 OpenERP SA (<http://www.openerp.com>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from osv import osv, fields
import logging
from tools.translate import _
import tools
from osv.orm import BrowseRecordError


class email_template_menu_wizard(osv.osv_memory):


    def template_action(self, cursor, user, ids, context=None):
        logging.info(context)
        template_id = self.browse(cursor, user, ids, context=context)[0].template_id.id
        template_obj = self.pool.get('email.template').browse(cursor, user, template_id, context=context)
        action_id = template_obj.ref_ir_act_window.id
        try:
            action = self.pool.get('ir.actions.act_window').browse(cursor, user, action_id, context=context)
        except BrowseRecordError:
            raise osv.except_osv(_("Warning"), _("No action exists for this template."))
        if not context:
            context = {}
        context['src_model'] = template_obj.object_name.model
        context['template_id'] = template_id
        #context['src_rec_id'] = context['active_id']
        #context['src_rec_ids'] = context['active_ids'] 
        return {
            'view_mode': action.view_mode,
            'view_type': action.view_type,
            'view_id': action.view_id and [action.view_id.id] or False,
            'res_model': action.res_model,
            'type': action.type,
            'target': action.target,
            'context': context
        }
        #return {'value': template_obj['ref_ir_act_window'].id}
        
    _name = 'email_template.menu.wizard'
    _description = 'This is the wizard for sending mail'
    _rec_name = "subject"

    

    _columns = {
        'template_id': fields.many2one('email.template', 'Template')
    }

    #FIXME: probably better by overriding default_get directly 
    _defaults = {
    }

    
email_template_menu_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
