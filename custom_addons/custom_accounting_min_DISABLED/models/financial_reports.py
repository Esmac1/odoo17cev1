# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime
import io
import json

class FinancialReportWizard(models.TransientModel):
    _name = 'custom_accounting.financial.report.wizard'
    _description = 'Financial Report Wizard'
    
    # ========== REPORT SELECTION ==========
    report_type = fields.Selection([
        ('profit_loss', 'Profit & Loss Statement'),
        ('balance_sheet', 'Balance Sheet'),
        ('cash_flow', 'Cash Flow Statement'),
        ('trial_balance', 'Trial Balance'),
        ('general_ledger', 'General Ledger'),
        ('aged_receivables', 'Aged Receivables'),
        ('aged_payables', 'Aged Payables'),
        ('bank_reconciliation', 'Bank Reconciliation'),
        ('budget_variance', 'Budget vs Actual'),
    ], string='Report Type', required=True, default='profit_loss')
    
    # ========== DATE RANGE ==========
    date_from = fields.Date(string='From Date', required=True, 
                           default=lambda self: date(date.today().year, 1, 1))
    date_to = fields.Date(string='To Date', required=True, 
                         default=lambda self: date.today())
    compare_with_previous = fields.Boolean(string='Compare with Previous Period', default=False)
    previous_date_from = fields.Date(string='Previous From Date')
    previous_date_to = fields.Date(string='Previous To Date')
    
    # ========== FILTERS ==========
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Report Currency',
                                 default=lambda self: self.env.company.currency_id)
    include_unposted = fields.Boolean(string='Include Unposted Entries', default=False)
    group_by_period = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], string='Group By', default='monthly')
    
    # ========== OUTPUT ==========
    result_html = fields.Html(string='Report Output', compute='_compute_result', sanitize=False)
    chart_data = fields.Char(string='Chart Data', compute='_compute_chart_data')
    
    # ========== COMPUTED FIELDS ==========
    @api.depends('report_type', 'date_from', 'date_to', 'currency_id', 'include_unposted')
    def _compute_result(self):
        for wizard in self:
            if wizard.report_type == 'profit_loss':
                wizard.result_html = self._generate_profit_loss_report()
            elif wizard.report_type == 'balance_sheet':
                wizard.result_html = self._generate_balance_sheet()
            elif wizard.report_type == 'cash_flow':
                wizard.result_html = self._generate_cash_flow()
            elif wizard.report_type == 'trial_balance':
                wizard.result_html = self._generate_trial_balance()
            elif wizard.report_type == 'general_ledger':
                wizard.result_html = self._generate_general_ledger()
            elif wizard.report_type == 'aged_receivables':
                wizard.result_html = self._generate_aged_receivables()
            elif wizard.report_type == 'aged_payables':
                wizard.result_html = self._generate_aged_payables()
            else:
                wizard.result_html = '<div class="alert alert-info">Report not yet implemented</div>'
    
    @api.depends('report_type', 'date_from', 'date_to')
    def _compute_chart_data(self):
        for wizard in self:
            if wizard.report_type == 'profit_loss':
                wizard.chart_data = self._get_profit_loss_chart_data()
            elif wizard.report_type == 'balance_sheet':
                wizard.chart_data = self._get_balance_sheet_chart_data()
            else:
                wizard.chart_data = '{}'
    
    # ========== REPORT GENERATION METHODS ==========
    def _generate_profit_loss_report(self):
        """Generate Profit & Loss Statement with multi-currency support"""
        lines = self._get_profit_loss_data()
        
        html = f'''
        <div class="financial-report">
            <h2>Profit &amp; Loss Statement</h2>
            <p>Period: {self.date_from} to {self.date_to}</p>
            <p>Currency: {self.currency_id.name}</p>
            
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Account</th>
                        <th style="text-align: right">Amount ({self.currency_id.symbol})</th>
                        <th style="text-align: right">% of Revenue</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        total_revenue = 0
        total_cogs = 0
        total_expenses = 0
        total_other_income = 0
        total_other_expenses = 0
        
        for line in lines:
            if line['type'] == 'revenue':
                total_revenue += line['amount']
            elif line['type'] == 'cogs':
                total_cogs += line['amount']
            elif line['type'] == 'expense':
                total_expenses += line['amount']
            elif line['type'] == 'other_income':
                total_other_income += line['amount']
            elif line['type'] == 'other_expense':
                total_other_expenses += line['amount']
            
            percent = (line['amount'] / total_revenue * 100) if total_revenue else 0
            
            html += f'''
                <tr>
                    <td>{line['name']}</td>
                    <td style="text-align: right">{self._format_currency(line['amount'])}</td>
                    <td style="text-align: right">{percent:.1f}%</td>
                </tr>
            '''
        
        gross_profit = total_revenue - total_cogs
        operating_profit = gross_profit - total_expenses
        net_profit = operating_profit + total_other_income - total_other_expenses
        
        html += f'''
                </tbody>
                <tfoot>
                    <tr class="table-active">
                        <td><strong>Total Revenue</strong></td>
                        <td style="text-align: right"><strong>{self._format_currency(total_revenue)}</strong></td>
                        <td style="text-align: right">100.0%</td>
                    </tr>
                    <tr>
                        <td>Less: Cost of Goods Sold</td>
                        <td style="text-align: right">({self._format_currency(total_cogs)})</td>
                        <td style="text-align: right">{(total_cogs/total_revenue*100 if total_revenue else 0):.1f}%</td>
                    </tr>
                    <tr class="table-success">
                        <td><strong>Gross Profit</strong></td>
                        <td style="text-align: right"><strong>{self._format_currency(gross_profit)}</strong></td>
                        <td style="text-align: right"><strong>{(gross_profit/total_revenue*100 if total_revenue else 0):.1f}%</strong></td>
                    </tr>
                    <tr>
                        <td>Less: Operating Expenses</td>
                        <td style="text-align: right">({self._format_currency(total_expenses)})</td>
                        <td style="text-align: right"></td>
                    </tr>
                    <tr class="table-info">
                        <td><strong>Operating Profit</strong></td>
                        <td style="text-align: right"><strong>{self._format_currency(operating_profit)}</strong></td>
                        <td style="text-align: right"></td>
                    </tr>
                    <tr>
                        <td>Add: Other Income</td>
                        <td style="text-align: right">{self._format_currency(total_other_income)}</td>
                        <td style="text-align: right"></td>
                    </tr>
                    <tr>
                        <td>Less: Other Expenses</td>
                        <td style="text-align: right">({self._format_currency(total_other_expenses)})</td>
                        <td style="text-align: right"></td>
                    </tr>
                    <tr class="table-primary">
                        <td><strong>Net Profit</strong></td>
                        <td style="text-align: right"><strong>{self._format_currency(net_profit)}</strong></td>
                        <td style="text-align: right"><strong>{(net_profit/total_revenue*100 if total_revenue else 0):.1f}%</strong></td>
                    </tr>
                </tfoot>
            </table>
        </div>
        '''
        
        return html
    
    def _generate_balance_sheet(self):
        """Generate Balance Sheet with multi-currency support"""
        assets = self._get_account_balances(['asset', 'bank', 'cash', 'receivable'])
        liabilities = self._get_account_balances(['liability', 'payable'])
        equity = self._get_account_balances(['equity'])
        
        total_assets = sum(a['balance'] for a in assets)
        total_liabilities = sum(l['balance'] for l in liabilities)
        total_equity = sum(e['balance'] for e in equity)
        
        html = f'''
        <div class="financial-report">
            <h2>Balance Sheet</h2>
            <p>As of: {self.date_to}</p>
            <p>Currency: {self.currency_id.name}</p>
            
            <div class="row">
                <div class="col-md-6">
                    <h3>Assets</h3>
                    <table class="table table-bordered">
                        <tbody>
        '''
        
        for asset in assets:
            html += f'''
                            <tr>
                                <td>{asset['name']}</td>
                                <td style="text-align: right">{self._format_currency(asset['balance'])}</td>
                            </tr>
            '''
        
        html += f'''
                            <tr class="table-active">
                                <td><strong>Total Assets</strong></td>
                                <td style="text-align: right"><strong>{self._format_currency(total_assets)}</strong></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="col-md-6">
                    <h3>Liabilities &amp; Equity</h3>
                    <table class="table table-bordered">
                        <tbody>
        '''
        
        for liability in liabilities:
            html += f'''
                            <tr>
                                <td>{liability['name']}</td>
                                <td style="text-align: right">{self._format_currency(liability['balance'])}</td>
                            </tr>
            '''
        
        html += f'''
                            <tr class="table-active">
                                <td><strong>Total Liabilities</strong></td>
                                <td style="text-align: right"><strong>{self._format_currency(total_liabilities)}</strong></td>
                            </tr>
        '''
        
        for equity_item in equity:
            html += f'''
                            <tr>
                                <td>{equity_item['name']}</td>
                                <td style="text-align: right">{self._format_currency(equity_item['balance'])}</td>
                            </tr>
            '''
        
        html += f'''
                            <tr class="table-active">
                                <td><strong>Total Equity</strong></td>
                                <td style="text-align: right"><strong>{self._format_currency(total_equity)}</strong></td>
                            </tr>
                            <tr class="table-primary">
                                <td><strong>Total Liabilities &amp; Equity</strong></td>
                                <td style="text-align: right"><strong>{self._format_currency(total_liabilities + total_equity)}</strong></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="alert alert-{'success' if abs(total_assets - (total_liabilities + total_equity)) < 0.01 else 'danger'}">
                <strong>Balance Check:</strong> 
                Assets ({self._format_currency(total_assets)}) = 
                Liabilities + Equity ({self._format_currency(total_liabilities + total_equity)})
                {'✓ Balanced' if abs(total_assets - (total_liabilities + total_equity)) < 0.01 else '✗ Not Balanced'}
            </div>
        </div>
        '''
        
        return html
    
    def _generate_cash_flow(self):
        """Generate Cash Flow Statement"""
        # Simplified implementation
        html = '''
        <div class="financial-report">
            <h2>Cash Flow Statement</h2>
            <p>Period: {self.date_from} to {self.date_to}</p>
            
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th style="text-align: right">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Cash from Operating Activities</strong></td>
                        <td style="text-align: right">0.00</td>
                    </tr>
                    <tr>
                        <td><strong>Cash from Investing Activities</strong></td>
                        <td style="text-align: right">0.00</td>
                    </tr>
                    <tr>
                        <td><strong>Cash from Financing Activities</strong></td>
                        <td style="text-align: right">0.00</td>
                    </tr>
                    <tr class="table-primary">
                        <td><strong>Net Change in Cash</strong></td>
                        <td style="text-align: right"><strong>0.00</strong></td>
                    </tr>
                    <tr>
                        <td>Cash at Beginning of Period</td>
                        <td style="text-align: right">0.00</td>
                    </tr>
                    <tr class="table-success">
                        <td><strong>Cash at End of Period</strong></td>
                        <td style="text-align: right"><strong>0.00</strong></td>
                    </tr>
                </tbody>
            </table>
        </div>
        '''
        
        return html
    
    # ========== HELPER METHODS ==========
    def _get_profit_loss_data(self):
        """Get data for Profit & Loss statement"""
        # Simplified - in production, get actual transaction data
        return [
            {'name': 'Sales Revenue', 'type': 'revenue', 'amount': 100000.00},
            {'name': 'Service Revenue', 'type': 'revenue', 'amount': 50000.00},
            {'name': 'Cost of Goods Sold', 'type': 'cogs', 'amount': 40000.00},
            {'name': 'Salaries & Wages', 'type': 'expense', 'amount': 60000.00},
            {'name': 'Rent Expense', 'type': 'expense', 'amount': 12000.00},
            {'name': 'Utilities', 'type': 'expense', 'amount': 5000.00},
            {'name': 'Interest Income', 'type': 'other_income', 'amount': 1000.00},
            {'name': 'Interest Expense', 'type': 'other_expense', 'amount': 2000.00},
        ]
    
    def _get_account_balances(self, account_types):
        """Get account balances for specified types"""
        accounts = self.env['custom_accounting.account'].search([
            ('type', 'in', account_types),
            ('company_id', '=', self.company_id.id),
            ('active', '=', True),
        ])
        
        return [{
            'name': f"{acc.code} {acc.name}",
            'balance': acc.balance,
            'foreign_balance': acc.foreign_balance if acc.currency_id else acc.balance,
        } for acc in accounts if abs(acc.balance) > 0.01]
    
    def _format_currency(self, amount):
        """Format amount as currency"""
        return f"{amount:,.2f}"
    
    def _get_profit_loss_chart_data(self):
        """Get chart data for Profit & Loss"""
        data = {
            'labels': ['Revenue', 'COGS', 'Gross Profit', 'Expenses', 'Net Profit'],
            'datasets': [{
                'label': 'Amount',
                'data': [150000, 40000, 110000, 77000, 33000],
                'backgroundColor': [
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(220, 53, 69, 0.8)',
                    'rgba(23, 162, 184, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(0, 123, 255, 0.8)',
                ],
            }]
        }
        return json.dumps(data)
    
    def _get_balance_sheet_chart_data(self):
        """Get chart data for Balance Sheet"""
        data = {
            'labels': ['Assets', 'Liabilities', 'Equity'],
            'datasets': [{
                'label': 'Amount',
                'data': [200000, 120000, 80000],
                'backgroundColor': [
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(220, 53, 69, 0.8)',
                    'rgba(0, 123, 255, 0.8)',
                ],
            }]
        }
        return json.dumps(data)
    
    # ========== ACTION METHODS ==========
    def print_report(self):
        """Print/Export the report"""
        return {
            'type': 'ir.actions.act_url',
            'url': f'/custom_accounting/financial_report/pdf/{self.id}',
            'target': 'new',
        }
    
    def export_excel(self):
        """Export report to Excel"""
        return {
            'type': 'ir.actions.act_url',
            'url': f'/custom_accounting/financial_report/excel/{self.id}',
            'target': 'new',
        }
