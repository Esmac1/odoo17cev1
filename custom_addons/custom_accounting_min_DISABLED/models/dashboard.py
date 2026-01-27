# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, timedelta

class AccountingDashboard(models.Model):
    _name = 'custom_accounting.dashboard'
    _description = 'Accounting Dashboard'
    _order = 'id desc'

    name = fields.Char(string="Name", default="Accounting Dashboard", readonly=True)

    # === KPIs ===
    total_revenue = fields.Float(string="Total Revenue", compute='_compute_kpis', store=False)
    total_expenses = fields.Float(string="Total Expenses", compute='_compute_kpis', store=False)
    net_income = fields.Float(string="Net Income", compute='_compute_kpis', store=False)
    cash_balance = fields.Float(string="Cash & Bank Balance", compute='_compute_kpis', store=False)
    accounts_receivable = fields.Float(string="Accounts Receivable", compute='_compute_kpis', store=False)
    accounts_payable = fields.Float(string="Accounts Payable", compute='_compute_kpis', store=False)
    total_assets = fields.Float(string="Total Assets", compute='_compute_kpis', store=False)
    total_liabilities = fields.Float(string="Total Liabilities", compute='_compute_kpis', store=False)
    equity = fields.Float(string="Equity", compute='_compute_kpis', store=False)

    # === Period ===
    period = fields.Selection([
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('quarter', 'This Quarter'),
        ('year', 'This Year'),
    ], default='month', string="Period")

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)

    @api.depends('period', 'company_id')
    def _compute_kpis(self):
        Account = self.env['custom_accounting.account']
        for dashboard in self:
            # Revenue & Expenses (P&L accounts)
            dashboard.total_revenue = sum(Account.search([
                ('type', '=', 'income'),
                ('company_id', '=', dashboard.company_id.id)
            ]).mapped('balance'))

            dashboard.total_expenses = sum(Account.search([
                ('type', '=', 'expense'),
                ('company_id', '=', dashboard.company_id.id)
            ]).mapped('balance'))

            dashboard.net_income = dashboard.total_revenue - dashboard.total_expenses

            # Cash & Bank
            cash_accounts = Account.search([
                ('code', 'in', ['900001', '900002']),
                ('company_id', '=', dashboard.company_id.id)
            ])
            dashboard.cash_balance = sum(cash_accounts.mapped('balance'))

            # AR / AP
            dashboard.accounts_receivable = sum(Account.search([
                ('type', '=', 'asset'),
                ('reconcile', '=', True),
                ('company_id', '=', dashboard.company_id.id)
            ]).mapped('balance'))

            dashboard.accounts_payable = sum(Account.search([
                ('type', '=', 'liability'),
                ('company_id', '=', dashboard.company_id.id)
            ]).mapped('balance'))

            # Balance Sheet Totals
            dashboard.total_assets = sum(Account.search([
                ('type', '=', 'asset'),
                ('company_id', '=', dashboard.company_id.id)
            ]).mapped('balance'))

            dashboard.total_liabilities = sum(Account.search([
                ('type', 'in', ['liability', 'equity']),
                ('company_id', '=', dashboard.company_id.id)
            ]).mapped('balance'))

            dashboard.equity = dashboard.total_assets - dashboard.total_liabilities
