# coding: utf-8
# Copyright (C) 2019 DynApps <http://www.dynapps.be>
# @author Stefan Rijnhart <stefan.rijnhart@dynapps.nl>
# @author Pieter Paulussen <pieter.paulussen@dynapps.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.tools import mute_logger
from psycopg2.extensions import QueryCanceledError
from openerp.tests.common import SavepointCase


class TestWebQueryTimeout(SavepointCase):
    def test_01_web_query_timeout(self):
        """ Time out exception occurs when setting a very short time out. The
        timeout model's search() method delays its result in testing mode
        especially for this purpose. """
        self.env['web.query.timeout']._register_hook()
        self.env['ir.config_parameter'].set_param(
            'web_query_timeout.timeout', '.01')
        self.assertEqual(self.env['web.query.timeout']._get_timeout(), 10)

        with self.assertRaises(QueryCanceledError):
            with mute_logger('openerp.sql_db'):
                with self.env.cr.savepoint():
                    self.env['web.query.timeout'].with_context(
                        statement_timeout=True).search([])

        # The time out does not occur without the context value
        self.env['web.query.timeout'].with_context(
            statement_timeout=False).search([])

        # The time out does not occur with a higher setting
        self.env['ir.config_parameter'].set_param(
            'web_query_timeout.timeout', '10')
        self.assertEqual(self.env['web.query.timeout']._get_timeout(), 10000)

        self.env['web.query.timeout'].with_context(
            statement_timeout=True).search([])
