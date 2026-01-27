# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, timedelta

class AccountingDashboard(models.Model):
    _name = 'custom_accounting.dashboard'
    _description = 'Accounting Dashboard'
    
    name = fields.Char(string='Name', default='Accounting Dashboard')
    
    # ===== KPI FIELDS =====
    total_revenue = fields.Float(string='Total Revenue', compute='_compute_kpis')
    total_expenses = fields.Float(string='Total Expenses', compute='_compute_kpis')
    net_income = fields.Float(string='Net Income', compute='_compute_kpis')
    cash_balance = fields.Float(string='Cash Balance', compute='_compute_kpis')
    accounts_receivable = fields.Float(string='Accounts Receivable', compute='_compute_kpis')
    accounts_payable = fields.Float(string='Accounts Payable', compute='_compute_kpis')
    total_assets = fields.Float(string='Total Assets', compute='_compute_kpis')
    total_liabilities = fields.Float(string='Total Liabilities', compute='_compute_kpis')
    equity = fields.Float(string='Equity', compute='_compute_kpis')
    
    # ===== FINANCIAL RATIOS =====
    current_ratio = fields.Float(string='Current Ratio', compute='_compute_ratios', digits=(12, 2))
    debt_ratio = fields.Float(string='Debt Ratio', compute='_compute_ratios', digits=(12, 2))
    profit_margin = fields.Float(string='Profit Margin', compute='_compute_ratios', digits=(12, 2))
    expense_ratio = fields.Float(string='Expense Ratio', compute='_compute_ratios', digits=(12, 2))
    quick_ratio = fields.Float(string='Quick Ratio', compute='_compute_ratios', digits=(12, 2))
    return_on_equity = fields.Float(string='Return on Equity', compute='_compute_ratios', digits=(12, 2))
    is_balanced = fields.Boolean(string='Is Balanced', compute='_compute_ratios')
    financial_health = fields.Selection([
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ], string='Financial Health', compute='_compute_ratios')
    cash_position = fields.Selection([
        ('positive', 'Positive'),
        ('negative', 'Negative'),
    ], string='Cash Position', compute='_compute_ratios')
    
    # ===== PERIOD SELECTION =====
    period = fields.Selection([
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('quarter', 'This Quarter'),
        ('year', 'This Year'),
        ('custom', 'Custom'),
    ], string='Period', default='month')
    
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date', default=fields.Date.today)
    
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related='company_id.currency_id', readonly=True)
    
    # ===== COMPUTED FIELDS =====
    @api.depends('period', 'date_from', 'date_to', 'company_id')
    def _compute_kpis(self):
        for dashboard in self:
            # Get date range
            date_from, date_to = dashboard._get_date_range()
            
            # Revenue (Income accounts)
            dashboard.total_revenue = dashboard._get_account_type_balance('income', date_from, date_to)
            
            # Expenses (Expense accounts)
            dashboard.total_expenses = dashboard._get_account_type_balance('expense', date_from, date_to)
            
            # Net Income
            dashboard.net_income = dashboard.total_revenue - dashboard.total_expenses
            
            # Cash Balance (Cash and Bank accounts)
            cash_accounts = dashboard.env['custom_accounting.account'].search([
                ('code', 'in', ['900001', '900002']),  # Your cash/bank accounts
                ('company_id', '=', dashboard.company_id.id)
            ])
            dashboard.cash_balance = sum(cash_accounts.mapped('balance'))
            
            # Accounts Receivable
            ar_accounts = dashboard.env['custom_accounting.account'].search([
                ('account_type', '=', 'asset'),
                ('reconcile', '=', True),
                ('company_id', '=', dashboard.company_id.id)
            ])
            dashboard.accounts_receivable = sum(ar_accounts.mapped('balance'))
            
            # Accounts Payable
            ap_accounts = dashboard.env['custom_accounting.account'].search([
                ('account_type', '=', 'liability'),
                ('company_id', '=', dashboard.company_id.id)
            ])
            dashboard.accounts_payable = sum(ap_accounts.mapped('balance'))
            
            # Total Assets
            asset_accounts = dashboard.env['custom_accounting.account'].search([
                ('account_type', '=', 'asset'),
                ('company_id', '=', dashboard.company_id.id)
            ])
            dashboard.total_assets = sum(asset_accounts.mapped('balance'))
            
            # Total Liabilities
            liability_accounts = dashboard.env['custom_accounting.account'].search([
                ('account_type', '=', 'liability'),
                ('company_id', '=', dashboard.company_id.id)
            ])
            dashboard.total_liabilities = sum(liability_accounts.mapped('balance'))
            
            # Equity
            equity_accounts = dashboard.env['custom_accounting.account'].search([
                ('account_type', '=', 'equity'),
                ('company_id', '=', dashboard.company_id.id)
            ])
            dashboard.equity = sum(equity_accounts.mapped('balance'))
    
    @api.depends('total_assets', 'total_liabilities', 'equity', 'net_income', 
                 'total_revenue', 'total_expenses', 'cash_balance', 'accounts_receivable', 'accounts_payable')
    def _compute_ratios(self):
        for dashboard in self:
            # Current Ratio (Assets / Liabilities)
            if dashboard.total_liabilities != 0:
                dashboard.current_ratio = dashboard.total_assets / dashboard.total_liabilities
            else:
                dashboard.current_ratio = 0
            
            # Debt Ratio (Liabilities / Assets)
            if dashboard.total_assets != 0:
                dashboard.debt_ratio = (dashboard.total_liabilities / dashboard.total_assets) * 100
            else:
                dashboard.debt_ratio = 0
            
            # Profit Margin (Net Income / Revenue)
            if dashboard.total_revenue != 0:
                dashboard.profit_margin = (dashboard.net_income / dashboard.total_revenue) * 100
            else:
                dashboard.profit_margin = 0
            
            # Expense Ratio (Expenses / Revenue)
            if dashboard.total_revenue != 0:
                dashboard.expense_ratio = (dashboard.total_expenses / dashboard.total_revenue) * 100
            else:
                dashboard.expense_ratio = 0
            
            # Quick Ratio ((Cash + Receivables) / Payables)
            if dashboard.accounts_payable != 0:
                dashboard.quick_ratio = (dashboard.cash_balance + dashboard.accounts_receivable) / dashboard.accounts_payable
            else:
                dashboard.quick_ratio = 0
            
            # Return on Equity (Net Income / Equity)
            if dashboard.equity != 0:
                dashboard.return_on_equity = (dashboard.net_income / dashboard.equity) * 100
            else:
                dashboard.return_on_equity = 0
            
            # Is Balanced (Assets = Liabilities + Equity)
            dashboard.is_balanced = abs(dashboard.total_assets - (dashboard.total_liabilities + dashboard.equity)) < 0.01
            
            # Financial Health
            if dashboard.total_liabilities == 0:
                dashboard.financial_health = 'healthy'
            elif dashboard.total_assets > dashboard.total_liabilities * 1.5:
                dashboard.financial_health = 'healthy'
            elif dashboard.total_assets > dashboard.total_liabilities:
                dashboard.financial_health = 'warning'
            else:
                dashboard.financial_health = 'critical'
            
            # Cash Position
            if dashboard.cash_balance > 0:
                dashboard.cash_position = 'positive'
            else:
                dashboard.cash_position = 'negative'
    
    # ===== HELPER METHODS =====
    def _get_date_range(self):
        """Get date range based on selected period"""
        today = date.today()
        
        if self.period == 'today':
            return today, today
        elif self.period == 'week':
            return today - timedelta(days=today.weekday()), today
        elif self.period == 'month':
            return date(today.year, today.month, 1), today
        elif self.period == 'quarter':
            quarter = (today.month - 1) // 3 + 1
            month_start = (quarter - 1) * 3 + 1
            return date(today.year, month_start, 1), today
        elif self.period == 'year':
            return date(today.year, 1, 1), today
        else:  # custom
            return self.date_from or date.today(), self.date_to or date.today()
    
    def _get_account_type_balance(self, account_type, date_from, date_to):
        """Get balance for account type in period"""
        accounts = self.env['custom_accounting.account'].search([
            ('account_type', '=', account_type),
            ('company_id', '=', self.company_id.id)
        ])
        
        total = 0
        for account in accounts:
            balance = self._get_account_balance(account, date_from, date_to)
            total += balance
        
        return total
    
    def _get_account_balance(self, account, date_from, date_to):
        """Get account balance for period"""
        domain = [
            ('account_id', '=', account.id),
            ('move_id.state', '=', 'posted'),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', self.company_id.id)
        ]
        
        lines = self.env['custom_accounting.move.line'].search(domain)
        return sum(lines.mapped('debit')) - sum(lines.mapped('credit'))
    
    # ===== ACTION METHODS =====
    def action_view_revenue(self):
        """View revenue accounts"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Revenue Accounts',
            'res_model': 'custom_accounting.account',
            'view_mode': 'tree,form',
            'domain': [('account_type', '=', 'income'), 
                      ('company_id', '=', self.company_id.id)],
            'context': {'search_default_active': 1},
        }
    
    def action_view_expenses(self):
        """View expense accounts"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expense Accounts',
            'res_model': 'custom_accounting.account',
            'view_mode': 'tree,form',
            'domain': [('account_type', '=', 'expense'),
                      ('company_id', '=', self.company_id.id)],
            'context': {'search_default_active': 1},
        }
    
    def action_view_cash(self):
        """View cash accounts"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cash Accounts',
            'res_model': 'custom_accounting.account',
            'view_mode': 'tree,form',
            'domain': [('code', 'in', ['900001', '900002']),
                      ('company_id', '=', self.company_id.id)],
        }
    
    def action_view_receivables(self):
        """View receivable accounts"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Accounts Receivable',
            'res_model': 'custom_accounting.account',
            'view_mode': 'tree,form',
            'domain': [('account_type', '=', 'asset'), ('reconcile', '=', True),
                      ('company_id', '=', self.company_id.id)],
        }
    
    def action_view_payables(self):
        """View payable accounts"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Accounts Payable',
            'res_model': 'custom_accounting.account',
            'view_mode': 'tree,form',
            'domain': [('account_type', '=', 'liability'),
                      ('company_id', '=', self.company_id.id)],
        }
    
    def action_view_assets(self):
        """View all assets"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assets',
            'res_model': 'custom_accounting.account',
            'view_mode': 'tree,form',
            'domain': [('account_type', '=', 'asset'),
                      ('company_id', '=', self.company_id.id)],
        }
    
    def action_view_liabilities(self):
        """View all liabilities"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Liabilities',
            'res_model': 'custom_accounting.account',
            'view_mode': 'tree,form',
            'domain': [('account_type', '=', 'liability'),
                      ('company_id', '=', self.company_id.id)],
        }
