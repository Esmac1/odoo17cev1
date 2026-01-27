# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PayrollSetupWizard(models.TransientModel):
    _name = 'custom_payroll.setup.wizard'
    _description = 'Payroll Setup Wizard'
    
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    
    create_all_accounts = fields.Boolean(string='Create All Payroll Accounts', default=True)
    create_bank_account = fields.Boolean(string='Create Bank Account', default=True)
    
    # Account selection options
    salary_expense_code = fields.Char(string='Salary Expense Code', default='900101')
    salary_payable_code = fields.Char(string='Salary Payable Code', default='900201')
    tax_payable_code = fields.Char(string='Tax Payable Code', default='900301')
    
    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        defaults['company_id'] = self.env.company.id
        return defaults
    
    def action_setup_payroll(self):
        """Setup payroll accounts for the company"""
        Account = self.env['custom_accounting.account']
        company = self.company_id
        
        # Check if accounts already exist
        existing_accounts = Account.search([
            ('payroll_account_type', '!=', 'none'),
            ('company_id', '=', company.id)
        ])
        
        if existing_accounts and not self.env.context.get('force'):
            return {
                'type': 'ir.actions.act_window',
                'name': 'Existing Accounts Found',
                'res_model': 'custom_payroll.setup.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'context': {'force': True},
            }
        
        created_accounts = []
        
        # Create basic payroll accounts
        basic_accounts = [
            {
                'name': f'Salary Expense - {company.name}',
                'code': self.salary_expense_code,
                'payroll_account_type': 'salary_expense',
                'account_type': 'expense',
                'account_category': 'payroll_expense',
            },
            {
                'name': f'Salaries Payable - {company.name}',
                'code': self.salary_payable_code,
                'payroll_account_type': 'salary_payable',
                'account_type': 'liability',
                'account_category': 'payroll_liability',
            },
            {
                'name': f'PAYE Tax Payable - {company.name}',
                'code': self.tax_payable_code,
                'payroll_account_type': 'tax_payable',
                'account_type': 'liability',
                'account_category': 'tax',
            },
        ]
        
        for acc_data in basic_accounts:
            account = Account.create({
                'name': acc_data['name'],
                'code': acc_data['code'],
                'account_type': acc_data['account_type'],
                'account_category': acc_data['account_category'],
                'payroll_account_type': acc_data['payroll_account_type'],
                'company_id': company.id,
                'created_from_payroll': True,
                'is_payroll_account': True,
            })
            created_accounts.append(account.name)
        
        # Create bank account if requested
        if self.create_bank_account:
            bank_account = Account.create({
                'name': f'Bank Account - {company.name}',
                'code': '900001',
                'account_type': 'asset',
                'account_category': 'cash_bank',
                'company_id': company.id,
                'reconcile': True,
            })
            created_accounts.append(bank_account.name)
        
        # Create additional accounts if requested
        if self.create_all_accounts:
            additional_accounts = [
                ('transport_expense', 'Transport Allowance', '900161', 'expense', 'payroll_expense'),
                ('housing_expense', 'Housing Allowance', '900171', 'expense', 'payroll_expense'),
                ('medical_expense', 'Medical Allowance', '900151', 'expense', 'payroll_expense'),
                ('overtime_expense', 'Overtime Expense', '900121', 'expense', 'payroll_expense'),
                ('bonus_expense', 'Bonus Expense', '900131', 'expense', 'payroll_expense'),
                ('pension_payable', 'Pension Payable', '900211', 'liability', 'payroll_liability'),
                ('nhif_payable', 'NHIF Payable', '900221', 'liability', 'payroll_liability'),
                ('loan_receivable', 'Employee Loan Receivable', '900401', 'asset', 'current_asset'),
            ]
            
            for acc_type, name, code, acc_type_field, category in additional_accounts:
                account = Account.create({
                    'name': f'{name} - {company.name}',
                    'code': code,
                    'account_type': acc_type_field,
                    'account_category': category,
                    'payroll_account_type': acc_type,
                    'company_id': company.id,
                    'created_from_payroll': True,
                    'is_payroll_account': True,
                })
                created_accounts.append(account.name)
        
        # Create payroll journal
        journal = self.env['custom_accounting.journal'].search([
            ('code', '=', 'PAY'),
            ('company_id', '=', company.id)
        ], limit=1)
        
        if not journal:
            journal = self.env['custom_accounting.journal'].create({
                'name': 'Payroll Journal',
                'code': 'PAY',
                'type': 'general',
                'company_id': company.id,
            })
        
        # Return success message
        message = _("""
        Payroll setup completed successfully!
        
        Created accounts:
        %s
        
        Payroll Journal: %s
        
        You can now process payroll.
        """) % ('\n'.join([f'• {name}' for name in created_accounts]), journal.name)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Payroll Setup Complete'),
                'message': message,
                'sticky': True,
                'type': 'success',
            }
        }
