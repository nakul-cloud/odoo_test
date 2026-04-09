# models/lead_activity.py
from odoo import models, fields

class LeadActivity(models.Model):
    _name = 'lead.activity'
    _description = 'Lead Activity Log'
    _order = 'create_date desc'
    
    lead_id = fields.Many2one('lead.generation', string='Lead', required=True, ondelete='cascade')
    activity_type = fields.Selection([
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('commented', 'Commented'),
        ('assigned', 'Assigned'),
        ('status_changed', 'Status Changed'),
    ], string='Activity Type', required=True)
    
    description = fields.Text(string='Description')
    # Captures the user responsible for the change when available.
    user_id = fields.Many2one('res.users', string='User')
    
    old_value = fields.Char(string='Old Value')
    new_value = fields.Char(string='New Value')
    field_name = fields.Char(string='Field Changed')
    
    api_token_id = fields.Many2one('lead.api.token', string='API Token Used')