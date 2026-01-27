odoo.define('custom_payroll.dashboard', function (require) {
    "use strict";
    
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var _t = core._t;
    
    var PayrollDashboard = AbstractAction.extend({
        template: 'CustomPayrollDashboard',
        
        events: {
            'click a[data-action]': '_onActionClick',
        },
        
        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.action_manager = parent;
        },
        
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._renderDashboard();
            });
        },
        
        _renderDashboard: function () {
            // Fetch and render dashboard data
            this._rpc({
                model: 'custom_payroll.payroll_dashboard',
                method: 'search_read',
                args: [[]],
                kwargs: {
                    limit: 12,
                    order: 'month DESC'
                }
            }).then(function (data) {
                // Process and display data
                console.log('Dashboard data:', data);
            });
        },
        
        _onActionClick: function (event) {
            event.preventDefault();
            var $target = $(event.currentTarget);
            var action = $target.data('action');
            var model = $target.data('model');
            
            if (action && model) {
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: $target.text().trim(),
                    res_model: model,
                    views: [[false, 'list'], [false, 'form']],
                    target: 'current'
                });
            }
        },
    });
    
    core.action_registry.add('custom_payroll_dashboard', PayrollDashboard);
    
    return PayrollDashboard;
});
