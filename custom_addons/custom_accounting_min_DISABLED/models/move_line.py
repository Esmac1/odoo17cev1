# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class CustomMoveLine(models.Model):
    _name = 'custom_accounting.move.line'
    _description = 'Journal Item'
    _order = 'date desc, id desc'

    # ========== BASIC FIELDS ==========
    move_id = fields.Many2one('custom_accounting.move', string='Journal Entry', 
                             required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Label', required=True)
    account_id = fields.Many2one('custom_accounting.account', string='Account', 
                                required=True, index=True, domain="[('active', '=', True)]")
    partner_id = fields.Many2one('res.partner', string='Partner', index=True)
    
    # ========== AMOUNTS ==========
    debit = fields.Float(string='Debit', default=0.0, digits=(16, 2))
    credit = fields.Float(string='Credit', default=0.0, digits=(16, 2))
    balance = fields.Float(string='Balance', compute='_compute_balance', store=True, digits=(16, 2))
    
    # ========== MULTI-CURRENCY SUPPORT ==========
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                 compute='_compute_currency', store=True)
    amount_currency = fields.Float(string='Amount in Currency', digits=(16, 2),
                                  help="Amount in the currency of the account")
    exchange_rate = fields.Float(string='Exchange Rate', digits=(12, 6),
                                help="Rate from transaction currency to company currency")
    
    # ========== DATES & COMPANY ==========
    date = fields.Date(string='Date', related='move_id.date', store=True, index=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                related='move_id.company_id', store=True, index=True)
    
    # ========== RECONCILIATION ==========
    reconciled = fields.Boolean(string='Reconciled', default=False, index=True)
    full_reconcile_id = fields.Many2one('custom_accounting.full.reconcile', string='Full Reconcile')
    
    # ========== ANALYTIC ACCOUNTING ==========
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    
    # ========== COMPUTED FIELDS ==========
    @api.depends('debit', 'credit')
    def _compute_balance(self):
        for line in self:
            line.balance = line.debit - line.credit
    
    @api.depends('account_id.currency_id')
    def _compute_currency(self):
        for line in self:
            line.currency_id = line.account_id.currency_id or self.env.company.currency_id
    
    # ========== CONSTRAINTS ==========
    @api.constrains('debit', 'credit')
    def _check_amounts(self):
        for line in self:
            if line.debit < 0 or line.credit < 0:
                raise ValidationError(_("Debit and Credit cannot be negative."))
            if line.debit > 0 and line.credit > 0:
                raise ValidationError(_("You cannot have both debit and credit on the same line."))
    
    @api.constrains('amount_currency', 'currency_id')
    def _check_currency_amount(self):
        for line in self:
            if line.currency_id and line.amount_currency == 0:
                raise ValidationError(_("Amount in currency cannot be zero for foreign currency transactions."))
    
    # ========== HELPER METHODS ==========
    def get_currency_amount(self, to_currency=None):
        """Convert amount to specified currency"""
        self.ensure_one()
        if not to_currency:
            to_currency = self.env.company.currency_id
        
        if self.currency_id == to_currency:
            return self.amount_currency
        
        # Convert using exchange rate
        rate = self.exchange_rate if self.exchange_rate else 1.0
        return self.amount_currency * rate
