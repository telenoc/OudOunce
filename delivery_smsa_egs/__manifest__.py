# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "SMSA Express Shipping Connector",
    'license': 'OPL-1',
    'description': "Send your shipping through SMSA and track them online",
    'category': 'Website',
    'summary': 'Send your shipping through SMSA and track them online',
    'version': '13.0.1.0',
    'author': 'Egregious Solutions',
    'website': 'https://egregioussolutions.com/',
    'maintainer': 'Egregious Solutions',
    'depends': ['delivery', 'mail'],
    'external_dependencies': {'python': ['zeep']},
    'data': [
        'data/product_data.xml',
        'views/delivery_smsa_view.xml',
        'views/stock_picking_view.xml'
    ],
    'uninstall_hook': 'uninstall_hook',
    'support': 'info@egregioussolutions.com',
    'application': True,
    'price': 99.00,
    'currency': 'EUR',
    'images': ['static/description/banner.png'],
}
