# coding: utf-8
# Copyright (C) 2019 DynApps <http://www.dynapps.be>
# @author Stefan Rijnhart <stefan.rijnhart@dynapps.nl>
# @author Pieter Paulussen <pieter.paulussen@dynapps.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Web Query Timeout',
    'version': '8.0.1.0.0',
    'author': 'Dynapps,Odoo Community Association',
    'website': 'https://github.com/OCA/Web',
    'license': 'AGPL-3',
    'category': 'Web',
    'depends': [
        'web',
    ],
    'data': [
        'data/ir_config_parameter.xml',
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/web_query_timeout.xml',
    ],
}
