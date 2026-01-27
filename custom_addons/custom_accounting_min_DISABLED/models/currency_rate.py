# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime

class CurrencyRate(models.Model):
    _name = 'custom_accounting.currency.rate'
    _description = 'Currency Exchange Rate'
    _order = 'date desc, currency_id'
    
    # ========== BASIC FIELDS ==========
    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today, index=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, index=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True, index=True)
    
    # ========== RATES ==========
    rate = fields.Float(string='Rate', digits=(12, 6), required=True,
                       help="1 unit of foreign currency = X units of company currency")
    inverse_rate = fields.Float(string='Inverse Rate', digits=(12, 6), compute='_compute_inverse_rate', store=True)
    
    # ========== SOURCE ==========
    source = fields.Selection([
        ('manual', 'Manual Entry'),
        ('bank', 'Bank Feed'),
        ('api', 'API Integration'),
        ('system', 'System Generated'),
    ], string='Source', default='manual')
    
    # ========== COMPUTED FIELDS ==========
    @api.depends('date', 'currency_id')
    def _compute_name(self):
        for rate in self:
            rate.name = f"{rate.currency_id.name} - {rate.date}"
    
    @api.depends('rate')
    def _compute_inverse_rate(self):
        for rate in self:
            rate.inverse_rate = 1.0 / rate.rate if rate.rate != 0 else 0.0
    
    # ========== CONSTRAINTS ==========
    _sql_constraints = [
        ('currency_date_company_uniq', 'UNIQUE(currency_id, date, company_id)', 
         'Only one rate per currency, date, and company is allowed!'),
    ]
    
    @api.constrains('rate')
    def _check_rate(self):
        for rate in self:
            if rate.rate <= 0:
                raise ValidationError(_('Exchange rate must be greater than zero.'))
    
    # ========== HELPER METHODS ==========
    @api.model
    def get_rate(self, currency_id, date=None, company_id=None):
        """Get exchange rate for a currency on specific date"""
        if not date:
            date = fields.Date.today()
        
        if not company_id:
            company_id = self.env.company.id
        
        rate = self.search([
            ('currency_id', '=', currency_id),
            ('date', '<=', date),
            ('company_id', '=', company_id),
        ], limit=1, order='date desc')
        
        return rate.rate if rate else 1.0
    
    def convert_amount(self, amount, from_currency, to_currency, date=None):
        """Convert amount from one currency to another"""
        if from_currency == to_currency:
            return amount
        
        # Get rate from foreign to company currency
        rate_from = self.get_rate(from_currency.id, date)
        rate_to = self.get_rate(to_currency.id, date)
        
        # Convert through company currency
        amount_in_company = amount * rate_from
        return amount_in_company / rate_to if rate_to != 0 else 0.0
