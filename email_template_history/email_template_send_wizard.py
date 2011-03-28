from osv import osv, fields
from tools.translate import _
import time


class email_template_send_wizard(osv.osv_memory):
    _name = 'email_template.send.wizard'
    _inherit = 'email_template.send.wizard'

    def save_to_mailbox(self, cr, uid, ids, context=None):
        template = self._get_template(cr, uid, context)
        screen_vals = self.read(cr, uid, ids[0], [],context)
        mail_ids = super(email_template_send_wizard, self).save_to_mailbox(cr, uid, ids, context)
        mail_objs = self.pool.get('email_template.mailbox').read(cr, uid, mail_ids)
        for idx, mail_obj in enumerate(mail_objs):
            partner_id = context['src_rec_ids'][idx]
            attachment_ids = self.pool.get('ir.attachment').search(cr, uid, [('res_id', '=', mail_obj['id'])])
            if template.report_template:
                data = {}
                data['model'] = self.pool.get('ir.model').browse(cr, uid, screen_vals['rel_model'], context).model
            if template.partner_event and self._get_template_value(cr, uid, 'partner_event', context):
                name = mail_obj['subject']
                if isinstance(name, str):
                    name = unicode(name, 'utf-8')
                if len(name) > 64:
                    name = name[:61] + '...'
                model = res_id = False
                if template.report_template and self.pool.get('res.request.link').search(cr, uid, [('object','=',data['model'])], context=context):
                    model = data['model']
                    res_id = partner_id
                elif attachment_ids and self.pool.get('res.request.link').search(cr, uid, [('object','=','ir.attachment')], context=context):
                    model = 'ir.attachment'
                    res_id = attachment_ids[0]
                
                cr.execute("SELECT state from ir_module_module where state='installed' and name = 'mail_gateway'")
                mail_gateway = cr.fetchall()
                if mail_gateway:
                    values = {
                        'history': True,
                        'name': name,
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'user_id': uid,
                        'email_from': mail_obj['email_from'] or None,
                        'email_to': mail_obj['email_to'] or None,
                        'email_cc': mail_obj['email_cc'] or None,
                        'email_bcc': mail_obj['email_bcc'] or None,
                        'message_id': mail_obj['id'],
                        'description': mail_obj['body_text'] and mail_obj['body_text'] or mail_obj['body_html'],
                        'partner_id': self.get_value(cr, uid, template, template.partner_event, context, partner_id),
                        'model': model,
                        'res_id': res_id,
                    }
                    self.pool.get('mailgate.message').create(cr, uid, values, context)
        return mail_ids
email_template_send_wizard()
