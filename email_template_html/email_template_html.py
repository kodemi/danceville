# -*- coding: utf-8 -*-

from osv import osv, fields
from tools.translate import _

class email_template_html(osv.osv):
    _name = "email.template"
    _inherit = "email.template"
email_template_html()
