{
    'name': 'Lead Generation',
    'version': '19.0.3.0.0',
    'category': 'Sales',
    'summary': 'Advanced Lead Management with REST API',
    'description': '''
        Complete lead generation system with:
        - Secure Token-based Authentication
        - Real-time Activity Logging
        - Webhook Integrations
        - Advanced Filtering & Analytics
        - Bulk Operations
        - Role-based Access Control
    ''',
    'author': 'Nakul',
    'depends': ['base', 'crm', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/lead_views.xml',
        'views/lead_api_token_views.xml',
        'views/lead_activity_views.xml',
        'views/lead_webhook_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}