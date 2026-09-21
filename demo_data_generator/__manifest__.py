{
    'name': 'Demo Data Generator',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': 'Generate ~500 realistic demo records across Sales, Purchase, '
               'Inventory, MRP, Accounting, CRM, Projects, HR and eCommerce',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/demo_run_views.xml',
        'views/res_config_settings_views.xml',
        'views/actions.xml',
        'data/ir_cron.xml',
    ],
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
