// Copyright (C) 2019 DynApps <http://www.dynapps.be>
// @author Stefan Rijnhart <stefan.rijnhart@dynapps.nl>
// @author Pieter Paulussen <pieter.paulussen@dynapps.be>
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

openerp.web_query_timeout = function(instance) {
    instance.web.Query.include({
        /* Catch magic value to emit a notification */
        _execute: function (options) {
            return this._super(options).then(function (records){
                if (records === 'WebQueryTimeoutException') {
                    instance.web.notification.warn('Error', 'Query time out', true);
                    return [];
                }
                return records;
            });
        }
    });
};
