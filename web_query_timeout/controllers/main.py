# coding: utf-8
# Copyright (C) 2019 DynApps <http://www.dynapps.be>
# @author Stefan Rijnhart <stefan.rijnhart@dynapps.nl>
# @author Pieter Paulussen <pieter.paulussen@dynapps.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from psycopg2.extensions import QueryCanceledError
from openerp.addons.web.controllers.main import DataSet
from openerp.exceptions import Warning as UserError
from openerp import _


class WebQueryTimeoutDataSet(DataSet):
    def do_search_read(self, model, fields=False, offset=0, limit=False,
                       domain=None, sort=None):
        """ Set the context value that triggers the database query duration
        limit. If the time out occurs, set a magic value for 'records' which
        is intercepted in the javascript part. """
        try:
            res = super(WebQueryTimeoutDataSet, self).do_search_read(
                model, fields=fields, offset=offset, limit=limit,
                domain=domain, sort=sort)
            return res
        except QueryCanceledError:
            return {
                'length': 0,
                'records': 'WebQueryTimeoutException',
            }

    def _call_kw(self, model, method, args, kwargs):
        """
        Trigger an user error instead of the QueryCanceledError with the
        large stacktrace that belongs to the error.
        """
        try:
            res = super(WebQueryTimeoutDataSet, self)._call_kw(
                model, method, args, kwargs)
            return res
        except QueryCanceledError:
            raise UserError(_('Query cancelled due to timeout'))
