from odoo import models, fields, api


class PropertyManagement(models.Model):
    _name = 'property.management'
    _description = 'Property Management'

    name = fields.Char(string='Property Name', required=True)
    description = fields.Text(string='Description')
    property_type = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('land', 'Land'),
    ], string='Property Type')
    price = fields.Float(string='Price')
    location = fields.Char(string='Location')
    status = fields.Selection([
        ('available', 'Available'),
        ('sold', 'Sold'),
        ('rented', 'Rented'),
    ], string='Status', default='available')
    create_date = fields.Datetime(string='Created Date', readonly=True)
