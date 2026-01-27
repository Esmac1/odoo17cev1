# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CustomTax(models.Model):
    _name = 'custom_accounting.tax'
    _description = 'Tax Definition'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(string="Short Code")
    rate = fields.Float(required=True, default=0.0)
    tax_type = fields.Selection([
        ('vat', 'VAT'),
        ('wht', 'Withholding Tax'),
        ('sales', 'Sales Tax'),
        ('other', 'Other')
    ], default='vat')
    account_id = fields.Many2one('custom_accounting.account', string='Tax Account', required=True)
    refund_account_id = fields.Many2one('custom_accounting.account', string='Tax Refund Account')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    
    # Add state field
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], default='draft', string='Status')
    
    tax_authority = fields.Selection([
        ('firs', 'FIRS'),
        ('lirs', 'LIRS'),
        ('others', 'Other State'),
    ], string='Tax Authority')
    tax_id_number = fields.Char(string='TIN')
    tax_certificate = fields.Char(string='Certificate No')
    effective_date = fields.Date(string='Effective Date')
    expiry_date = fields.Date(string='Expiry Date')
    
    is_withholding = fields.Boolean(string='Withholding Tax', default=False)
    price_include = fields.Boolean(string='Included in Price', default=False)
    
    def action_compute_sample(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sample Computation',
                'message': 'This is a sample tax computation.',
                'type': 'info',
            }
        }
