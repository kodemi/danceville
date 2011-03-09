# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _

class email_template_menu(osv.osv):
    _name = "email.template"
    _inherit = "email.template"
    
    def create_action(self, cr, uid, ids, context=None):
        super(email_template_menu, self).create_action(cr, uid, ids, context)
        ref_ir_value_id = self.browse(cr, uid, ids, context)[0].ref_ir_value.id
        self.pool.get('ir.values').write(cr, uid, ref_ir_value_id, {'key2': False}, context)
        return True
        
email_template_menu()
