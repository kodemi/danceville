# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _


class email_template(osv.osv):
    _name = "email.template"
    _inherit = "email.template"
        
    _columns = {
        'partner_event': fields.char(
                'Partner ID to log Events',
                size=250,
                help="Partner ID who an email event is logged.\n"
                "Placeholders can be used here. eg. ${object.partner_id.id}\n"
                "You must install the mail_gateway module to see the mail events "
                "in partner form.\nIf you also want to record the link to the "
                "object that sends the email, you must to add this object in the "
                "'Administration/Low Level Objects/Requests/Accepted Links in "
                "Requests' menu (or 'ir.attachment' to record the attachments)."),
    }
email_template()
