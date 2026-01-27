# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class PayrollAccountMixin(models.AbstractModel):
    """Mixin to handle payroll account lookups"""
    _name = 'payroll.account.mixin'
    _description = 'Payroll Account Mixin'
    
    def _get_payroll_account(self, account_type_code, company_id=None):
        """
        Get payroll account by payroll_account_type
        Args:
            account_type_code (str): payroll_account_type value
            company_id (int): Company ID (defaults to current company)
        Returns:
            custom_accounting.account record
        """
        if not account_type_code or account_type_code == 'none':
            raise UserError(_("Invalid payroll account type"))
        
        company_id = company_id or self.env.company.id
        
        # Search for the account
        account = self.env['custom_accounting.account'].search([
            ('payroll_account_type', '=', account_type_code),
            ('company_id', '=', company_id),
            ('active', '=', True)
        ], limit=1)
        
        if account:
            return account
        
        # Account not found - try to create it
        account = self._create_missing_payroll_account(account_type_code, company_id)
        
        if not account:
            raise UserError(_(
                "Payroll account for type '%s' not found. "
                "Please setup payroll accounts in Accounting → Payroll Accounts."
            ) % account_type_code)
        
        return account
    
    def _create_missing_payroll_account(self, account_type_code, company_id):
        """Create missing payroll account automatically"""
        # Mapping of payroll account types to account details
        account_mapping = {
            'salary_expense': {
                'name': 'Salary Expense',
                'account_category': 'payroll_expense',
                'account_type': 'expense',
                'code_range': (900101, 900110),
            },
            'wages_expense': {
                'name': 'Wages Expense',
                'account_category': 'payroll_expense',
                'account_type': 'expense',
                'code_range': (900111, 900120),
            },
            'overtime_expense': {
                'name': 'Overtime Expense',
                'account_category': 'payroll_expense',
                'account_type': 'expense',
                'code_range': (900121, 900130),
            },
            'bonus_expense': {
                'name': 'Bonus Expense',
                'account_category': 'payroll_expense',
                'account_type': 'expense',
                'code_range': (900131, 900140),
            },
            'commission_expense': {
                'name': 'Commission Expense',
                'account_category': 'payroll_expense',
                'account_type': 'expense',
                'code_range': (900141, 900150),
            },
            'medical_expense': {
                'name': 'Medical Allowance',
                'account_category': 'payroll_expense',
                'account_type': 'expense',
                'code_range': (900151, 900160),
            },
            'transport_expense': {
                'name': 'Transport Allowance',
                'account_category': 'payroll_expense',
                'account_type': 'expense',
                'code_range': (900161, 900170),
            },
            'housing_expense': {
                'name': 'Housing Allowance',
                'account_category': 'payroll_expense',
                'account_type': 'expense',
                'code_range': (900171, 900180),
            },
            'other_allowance_expense': {
                'name': 'Other Allowances',
                'account_category': 'payroll_expense',
                'account_type': 'expense',
                'code_range': (900181, 900190),
            },
            'salary_payable': {
                'name': 'Salaries Payable',
                'account_category': 'payroll_liability',
                'account_type': 'liability',
                'code_range': (900201, 900210),
            },
            'tax_payable': {
                'name': 'PAYE Tax Payable',
                'account_category': 'tax',
                'account_type': 'liability',
                'code_range': (900301, 900310),
            },
            'pension_payable': {
                'name': 'Pension Payable',
                'account_category': 'payroll_liability',
                'account_type': 'liability',
                'code_range': (900211, 900220),
            },
            'nhif_payable': {
                'name': 'NHIF Payable',
                'account_category': 'payroll_liability',
                'account_type': 'liability',
                'code_range': (900221, 900230),
            },
            'nssf_payable': {
                'name': 'NSSF Payable',
                'account_category': 'payroll_liability',
                'account_type': 'liability',
                'code_range': (900231, 900240),
            },
            'loan_receivable': {
                'name': 'Employee Loan Receivable',
                'account_category': 'current_asset',
                'account_type': 'asset',
                'code_range': (900401, 900410),
            },
            'advance_payable': {
                'name': 'Advance Salary Payable',
                'account_category': 'payroll_liability',
                'account_type': 'liability',
                'code_range': (900241, 900250),
            },
            'other_deduction_payable': {
                'name': 'Other Deductions Payable',
                'account_category': 'payroll_liability',
                'account_type': 'liability',
                'code_range': (900251, 900260),
            },
            'gratuity_expense': {
                'name': 'Gratuity Expense',
                'account_category': 'payroll_expense',
                'account_type': 'expense',
                'code_range': (900191, 900200),
            },
            'gratuity_payable': {
                'name': 'Gratuity Payable',
                'account_category': 'payroll_liability',
                'account_type': 'liability',
                'code_range': (900261, 900270),
            },
        }
        
        if account_type_code not in account_mapping:
            _logger.warning(f"Unknown payroll account type: {account_type_code}")
            return False
        
        mapping = account_mapping[account_type_code]
        company = self.env['res.company'].browse(company_id)
        
        # Find available code in range
        start_code, end_code = mapping['code_range']
        existing_codes = self.env['custom_accounting.account'].search([
            ('company_id', '=', company_id),
            ('code', '>=', str(start_code)),
            ('code', '<=', str(end_code))
        ]).mapped('code')
        
        code = None
        for num in range(start_code, end_code + 1):
            if str(num) not in existing_codes:
                code = str(num)
                break
        
        if not code:
            code = str(start_code)  # Fallback
        
        try:
            # Create the account
            account = self.env['custom_accounting.account'].create({
                'name': f"{mapping['name']} - {company.name}",
                'code': code,
                'account_type': mapping['account_type'],
                'account_category': mapping['account_category'],
                'payroll_account_type': account_type_code,
                'company_id': company_id,
                'created_from_payroll': True,
                'is_payroll_account': True,
            })
            
            _logger.info(f"Created missing payroll account: {account.name} ({account.code})")
            return account
            
        except Exception as e:
            _logger.error(f"Failed to create payroll account {account_type_code}: {e}")
            return False
    
    def _get_bank_account(self, company_id=None):
        """Get company's default bank account for salary payments"""
        company_id = company_id or self.env.company.id
        
        # First try to find cash/bank account
        bank_account = self.env['custom_accounting.account'].search([
            ('account_category', '=', 'cash_bank'),
            ('company_id', '=', company_id),
            ('active', '=', True)
        ], limit=1)
        
        if not bank_account:
            # Create a default bank account
            bank_account = self.env['custom_accounting.account'].create({
                'name': f'Bank Account - {self.env["res.company"].browse(company_id).name}',
                'code': '900001',
                'account_type': 'asset',
                'account_category': 'cash_bank',
                'company_id': company_id,
                'reconcile': True,
            })
        
        return bank_account
    
    def _validate_payroll_accounts(self, company_id=None):
        """Validate all required payroll accounts exist"""
        company_id = company_id or self.env.company.id
        
        required_accounts = [
            'salary_expense',
            'salary_payable',
            'tax_payable',
        ]
        
        missing = []
        for acc_type in required_accounts:
            account = self.env['custom_accounting.account'].search([
                ('payroll_account_type', '=', acc_type),
                ('company_id', '=', company_id),
                ('active', '=', True)
            ], limit=1)
            
            if not account:
                missing.append(acc_type)
        
        if missing:
            account_names = {
                'salary_expense': 'Salary Expense',
                'salary_payable': 'Salary Payable',
                'tax_payable': 'PAYE Tax Payable',
            }
            
            missing_names = [account_names.get(m, m) for m in missing]
            raise UserError(_(
                "Missing payroll accounts: %s\n"
                "Please setup payroll accounts in Accounting → Payroll Accounts."
            ) % ", ".join(missing_names))
        
        return True
