{
    'name': 'Lead Generation',
    'version': '19.0.2.0.0',  # Bumped version
    'category': 'Sales',
    'summary': 'Manage property leads and follow-ups with REST API',
    'description': 'Custom module for capturing and managing property sales leads with REST API endpoints',
    'author': 'Nakul',
    'depends': ['base', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/lead_views.xml',
    ],
    'installable': True,
    'application': True,
}