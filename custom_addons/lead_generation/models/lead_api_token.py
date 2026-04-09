# models/lead_api_token.py
from odoo import models, fields, api
import secrets
from datetime import timedelta

class LeadAPIToken(models.Model):
    _name = 'lead.api.token'
    _description = 'API Token for Lead Generation'
    _order = 'create_date desc'

    _sql_constraints = [
        ('token_unique', 'unique(token)', 'Token must be unique.'),
    ]
    
    name = fields.Char(string='Token Name', required=True)
    # Stored token value used for API authentication.
    token = fields.Char(string='Token', readonly=True, unique=True)
    user_id = fields.Many2one('res.users', string='User', required=True)
    is_active = fields.Boolean(string='Active', default=True)
    last_used = fields.Datetime(string='Last Used')
    expires_at = fields.Datetime(string='Expires At')
    
    # Scopes are used by controller decorators for access checks.
    scopes = fields.Selection([
        ('read', 'Read Only'),
        ('write', 'Read & Write'),
        ('admin', 'Admin'),
    ], string='Scope', default='read', required=True)
    
    ip_whitelist = fields.Text(string='IP Whitelist', help='Comma-separated IPs')
    rate_limit = fields.Integer(string='Rate Limit (req/min)', default=60)
    
    api_calls_count = fields.Integer(string='Total API Calls', default=0)
    
    @api.model
    def generate_token(self, name, user_id, scope='read', expires_days=30):
        """Generate a new API token"""
        token = secrets.token_urlsafe(32)
        expires_at = fields.Datetime.now() + timedelta(days=expires_days)
        
        return self.create({
            'name': name,
            'token': token,
            'user_id': user_id,
            'scopes': scope,
            'expires_at': expires_at,
        })
    
    def revoke(self):
        """Revoke this token"""
        self.write({'is_active': False})
    
    def verify_token(self, token_str):
        """Verify if token is valid"""
        if self.token != token_str:
            return False
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < fields.Datetime.now():
            return False
        return True
    
    def log_api_call(self):
        """Log this API call"""
        self.write({
            'last_used': fields.Datetime.now(),
            'api_calls_count': self.api_calls_count + 1,
        })