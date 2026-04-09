from odoo import models, fields


class Lead(models.Model):
    _name = 'lead.generation'
    _description = 'Lead Generation'
    _order = 'create_date desc'

    name = fields.Char(string='Lead Name', required=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone Number')
    company = fields.Char(string='Company Name')
    
    # Lead source helps reporting and attribution.
    lead_source = fields.Selection([
        ('website', 'Website'),
        ('phone', 'Phone Call'),
        ('email', 'Email'),
        ('social_media', 'Social Media'),
        ('referral', 'Referral'),
        ('walk_in', 'Walk In'),
        ('other', 'Other'),
    ], string='Lead Source', default='website', required=True)
    
    status = fields.Selection([
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('proposal_sent', 'Proposal Sent'),
        ('negotiation', 'In Negotiation'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ], string='Status', default='new', required=True)
    
    # Optional ownership for routing and accountability.
    user_id = fields.Many2one('res.users', string='Assigned User')

    budget = fields.Float(string='Budget')
    expected_closing_date = fields.Date(string='Expected Closing Date')
    notes = fields.Text(string='Notes')
    
    active = fields.Boolean(string='Active', default=True)
