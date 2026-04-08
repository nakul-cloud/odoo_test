{
    'name': 'Lead Generation',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Manage property leads and follow-ups',
    'description': 'Custom module for capturing and managing property sales leads',
    'author': 'Nakul',
    'depends': ['base', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/lead_views.xml',
    ],
    'installable': True,
    'application': True,
}
