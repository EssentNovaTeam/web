# coding: utf-8
# Copyright (C) 2019 DynApps <http://www.dynapps.be>
# @author Stefan Rijnhart <stefan.rijnhart@dynapps.nl>
# @author Pieter Paulussen <pieter.paulussen@dynapps.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from psycopg2.extensions import QueryCanceledError
import threading
from openerp import api, fields, models
from openerp.sql_db import db_connect
from openerp.tools import ormcache


class WebQueryTimeout(models.Model):
    _name = 'web.query.timeout'
    _order = 'id desc'
    _rec_name = 'domain'

    create_date = fields.Datetime(string='Timestamp')
    create_uid = fields.Many2one('res.users', string='User')
    domain = fields.Char(readonly=True, required=True)
    model = fields.Char(readonly=True, required=True)

    @ormcache(skiparg=1)
    @api.model
    def _get_timeout(self):
        """ Fetch time out and convert to miliseconds """
        key = 'web_query_timeout.timeout'
        timeout = self.env['ir.config_parameter'].with_context(
            statement_timeout=False).get_param(key)
        if timeout:
            try:
                res = int(1000 * float(timeout))
                return res
            except (TypeError, ValueError) as e:
                logging.getLogger(__name__).error(
                    "%s for %s value '%s'", e, key, timeout)
        return 0

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False,
                access_rights_uid=None):
        """ Fire a short delay in test mode to trigger the timeout """
        res = super(WebQueryTimeout, self)._search(
            args, offset=offset, limit=limit, order=order,
            count=count, access_rights_uid=access_rights_uid)
        if getattr(threading.currentThread(), 'testing', False):
            self.env.cr.execute('SELECT pg_sleep(.1)')
        return res

    def _register_hook(self, cr):
        """ Monkeypatch the basemodel's _search method to apply the query
        timeout when triggered from the context """
        BaseModel = models.BaseModel
        if not hasattr(BaseModel, '_web_query_timeout_search'):

            @api.model
            def _search(self, args, offset=0, limit=None, order=None,
                        count=False, access_rights_uid=None):
                """ If `web_query_timeout` is installed in this database, apply
                the timeout if the key `statement_timeout` is truthy in the
                context """
                timeout_model = None
                try:
                    timeout_model = self.env['web.query.timeout']
                except KeyError:
                    pass

                if timeout_model is not None and self.env.context.get(
                        'statement_timeout'):
                    timeout = timeout_model._get_timeout()
                    if timeout:
                        self.env.cr.execute(
                            "SET LOCAL statement_timeout = %s", (timeout,))

                try:
                    res = self._web_query_timeout_search(
                        args, offset=offset, limit=limit, order=order,
                        count=count, access_rights_uid=access_rights_uid)
                except QueryCanceledError:
                    with db_connect(self.env.cr.dbname).cursor() as new_cr:
                        self.env(cr=new_cr)['web.query.timeout'].create({
                            'domain': unicode(args),
                            'model': self._name,
                        })
                    raise

                return res

            BaseModel._web_query_timeout_search = BaseModel._search
            BaseModel._search = _search

        return super(WebQueryTimeout, self)._register_hook(cr)
