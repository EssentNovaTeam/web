# coding: utf-8
# Copyright (C) 2019 DynApps <http://www.dynapps.be>
# @author Stefan Rijnhart <stefan.rijnhart@dynapps.nl>
# @author Pieter Paulussen <pieter.paulussen@dynapps.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, api


class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    @api.model
    def create(self, vals):
        """ Clear query timeout parameter cache if necessary """
        res = super(IrConfigParameter, self).create(vals)
        if vals.get('key') == 'web_query_timeout.timeout':
            self.env['web.query.timeout']._get_timeout.clear_cache(
                self.env['web.query.timeout'])
        return res

    @api.multi
    def write(self, vals):
        """ Clear query timeout parameter cache if necessary """
        to_clear = self.filtered(
            lambda icp: icp.key == 'web_query_timeout.timeout')
        res = super(IrConfigParameter, self).write(vals)
        if to_clear or vals.get('key') == 'web_query_timeout.timeout':
            self.env['web.query.timeout']._get_timeout.clear_cache(
                self.env['web.query.timeout'])
        return res
