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
    groupby = fields.Char(readonly=True, required=False)
    fields_list = fields.Char(readonly=True, required=False)
    func_call = fields.Char(readonly=True, required=True)

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

    def _register_hook(self, cr):
        """
        Monkeypatch the basemodel methods to apply the query timeout when
        triggered from the context.
        """
        BaseModel = models.BaseModel

        def search_override():
            """
            Override the `_search` function to apply the web_query_timeout logic.
            """
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
                            'func_call': 'search'
                        })
                    raise

                return res

            BaseModel._web_query_timeout_search = BaseModel._search
            BaseModel._search = _search

        def read_group_override():
            """
            Override the `read_group` function to apply the web_query_timeout
            logic.
            """
            @api.model
            def read_group(self, domain, fields, groupby, offset=0, limit=None,
                           orderby=False, lazy=True, context=None):
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
                    res = self._web_query_timeout_read_group(
                        domain, fields, groupby, offset=offset, limit=limit,
                        orderby=orderby, lazy=lazy, context=context)
                except QueryCanceledError:
                    with db_connect(self.env.cr.dbname).cursor() as new_cr:
                        self.env(cr=new_cr)['web.query.timeout'].create({
                            'domain': unicode(domain),
                            'fields_list': unicode(fields),
                            'groupby': unicode(groupby),
                            'model': self._name,
                            'func_call': 'group_by'
                        })
                    raise

                return res

            BaseModel._web_query_timeout_read_group = BaseModel.read_group
            BaseModel.read_group = read_group

        if not hasattr(BaseModel, '_web_query_timeout_search'):
            search_override()
            read_group_override()

        return super(WebQueryTimeout, self)._register_hook(cr)
