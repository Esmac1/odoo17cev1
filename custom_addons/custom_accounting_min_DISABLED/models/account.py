# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CustomAccount(models.Model):
    _name = 'custom_accounting.account'
    _description = 'Account'
    _rec_name = 'complete_name'
    _order = 'code'
    
    # ========== BASIC FIELDS ==========
    name = fields.Char(string='Account Name', required=True, index=True)
    code = fields.Char(string='Account Code', required=True, index=True)
    complete_name = fields.Char(string='Complete Name', compute='_compute_complete_name', 
                               recursive=True, store=True, index=True)
    
    # ========== HIERARCHY ==========
    parent_id = fields.Many2one('custom_accounting.account', string='Parent Account', 
                               index=True, ondelete='cascade')
    child_ids = fields.One2many('custom_accounting.account', 'parent_id', string='Child Accounts')
    level = fields.Integer(string='Level', compute='_compute_level', store=True)
    
    # ========== CLASSIFICATION ==========
    type = fields.Selection([
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('income', 'Income'),
        ('expense', 'Expense'),
        ('bank', 'Bank'),
        ('cash', 'Cash'),
        ('receivable', 'Receivable'),
        ('payable', 'Payable'),
    ], string='Account Type', required=True, default='expense', index=True)
    
    # ========== MULTI-CURRENCY SUPPORT ==========
    currency_id = fields.Many2one('res.currency', string='Account Currency',
                                 help="If set, transactions in this account must be in this currency")
    allow_multicurrency = fields.Boolean(string='Allow Multi-Currency', default=False,
                                        help="Allow transactions in multiple currencies")
    reconcile = fields.Boolean(string='Allow Reconciliation', default=False,
                              help="Used for accounts that can be reconciled (bank, receivable, payable)")
    
    # ========== COMPANY ==========
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True, index=True)
    
    # ========== STATUS ==========
    active = fields.Boolean(string='Active', default=True, index=True)
    note = fields.Text(string='Internal Notes')
    
    # ========== COMPUTED FIELDS ==========
    balance = fields.Float(string='Balance', compute='_compute_balance', store=True, digits=(16, 2))
    foreign_balance = fields.Float(string='Foreign Balance', compute='_compute_foreign_balance', digits=(16, 2))
    currency_symbol = fields.Char(string='Currency Symbol', compute='_compute_currency_symbol')
    
    # ========== CONSTRAINTS ==========
    _sql_constraints = [
        ('code_company_uniq', 'UNIQUE(code, company_id)', 'Account code must be unique per company!'),
        ('name_company_uniq', 'UNIQUE(name, company_id)', 'Account name must be unique per company!'),
    ]
    
    # ========== COMPUTE METHODS ==========
    @api.depends('name', 'code', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for account in self:
            if account.parent_id:
                account.complete_name = f'{account.parent_id.complete_name} / {account.code} {account.name}'
            else:
                account.complete_name = f'{account.code} {account.name}'
    
    @api.depends('parent_id')
    def _compute_level(self):
        for account in self:
            level = 0
            parent = account.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            account.level = level
    
    @api.depends('currency_id')
    def _compute_currency_symbol(self):
        for account in self:
            account.currency_symbol = account.currency_id.symbol if account.currency_id else ''
    
    @api.depends_context('company_id', 'currency_id')
    def _compute_balance(self):
        # Simplified - in production, this would compute from actual transactions
        for account in self:
            account.balance = 0.0
    
    @api.depends('balance', 'currency_id')
    def _compute_foreign_balance(self):
        for account in self:
            if account.currency_id and account.currency_id != self.env.company.currency_id:
                # Convert to account currency
                rate = account.currency_id.rate if account.currency_id.rate > 0 else 1.0
                account.foreign_balance = account.balance / rate
            else:
                account.foreign_balance = account.balance
    
    # ========== CONSTRAINTS ==========
    @api.constrains('parent_id')
    def _check_parent_id(self):
        for account in self:
            if account.parent_id and account.parent_id == account:
                raise ValidationError(_('An account cannot be its own parent!'))
    
    @api.constrains('currency_id', 'type')
    def _check_currency_account_type(self):
        for account in self:
            if account.currency_id and account.type not in ['bank', 'cash', 'receivable', 'payable']:
                raise ValidationError(_('Currency can only be set on Bank, Cash, Receivable, or Payable accounts!'))
