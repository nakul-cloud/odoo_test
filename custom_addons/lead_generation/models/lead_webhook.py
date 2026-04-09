from odoo import models, fields


class LeadWebhook(models.Model):
    _name = 'lead.webhook'
    _description = 'Lead Webhook'
    _order = 'create_date desc'

    name = fields.Char(string='Name', required=True)
    # Target URL called when events occur.
    url = fields.Char(string='Webhook URL', required=True)
    is_active = fields.Boolean(string='Active', default=True)

    event_type = fields.Selection([
        ('all', 'All Events'),
        ('lead_created', 'Lead Created'),
        ('lead_updated', 'Lead Updated'),
        ('lead_deleted', 'Lead Deleted'),
    ], string='Event Type', default='all', required=True)

    # Optional secret used to sign payloads.
    secret = fields.Char(string='Secret')
    headers = fields.Text(string='Custom Headers (JSON)')