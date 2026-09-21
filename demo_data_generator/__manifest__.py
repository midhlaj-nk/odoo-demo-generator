{
    'name': 'Demo Data Generator',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Generate ~500 realistic demo records across Sales, Purchase, '
               'Inventory, MRP, Accounting, CRM, Projects, HR and eCommerce',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': ['views/actions.xml'],
    'assets': {
        'web.assets_backend': [
            'demo_data_generator/static/src/demo_generator.scss',
            'demo_data_generator/static/src/demo_generator.xml',
            'demo_data_generator/static/src/demo_generator.js',
        ],
    },
    'application': True,
    'installable': True,
}
