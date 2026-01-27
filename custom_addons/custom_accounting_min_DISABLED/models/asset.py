# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime

class Asset(models.Model):
    _name = 'custom_accounting.asset'
    _description = 'Fixed Asset'
    _order = 'code, name'
    
    # Basic Information
    name = fields.Char(string='Asset Name', required=True)
    code = fields.Char(string='Asset Code', required=True, default=lambda self: self.env['ir.sequence'].next_by_code('custom_accounting.asset'))
    category_id = fields.Many2one('custom_accounting.asset.category', string='Asset Category', required=True)
    
    # Acquisition
    purchase_date = fields.Date(string='Purchase Date', required=True, default=fields.Date.today)
    purchase_value = fields.Float(string='Purchase Value', required=True, digits=(16, 2))
    salvage_value = fields.Float(string='Salvage Value', digits=(16, 2), default=0.0)
    useful_life = fields.Integer(string='Useful Life (Months)', required=True, default=60)
    
    # Depreciation
    depreciation_method = fields.Selection([
        ('straight_line', 'Straight Line'),
        ('declining_balance', 'Declining Balance'),
        ('double_declining', 'Double Declining Balance')
    ], string='Depreciation Method', required=True, default='straight_line')
    
    depreciation_rate = fields.Float(string='Depreciation Rate (%)', compute='_compute_depreciation_rate')
    accumulated_depreciation = fields.Float(string='Accumulated Depreciation', compute='_compute_accumulated_depreciation', store=True)
    current_value = fields.Float(string='Current Value', compute='_compute_current_value', store=True)
    
    # Accounting
    asset_account_id = fields.Many2one('custom_accounting.account', string='Asset Account', required=True)
    depreciation_account_id = fields.Many2one('custom_accounting.account', string='Depreciation Account', required=True)
    expense_account_id = fields.Many2one('custom_accounting.account', string='Expense Account', required=True)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('closed', 'Closed'),
        ('sold', 'Sold'),
        ('scrapped', 'Scrapped')
    ], string='Status', default='draft', required=True)
    
    # Depreciation Lines
    depreciation_line_ids = fields.One2many('custom_accounting.asset.depreciation.line', 'asset_id', string='Depreciation Lines')
    
    # Computed fields
    @api.depends('depreciation_method', 'useful_life')
    def _compute_depreciation_rate(self):
        for asset in self:
            if asset.useful_life > 0:
                if asset.depreciation_method == 'straight_line':
                    asset.depreciation_rate = 100.0 / asset.useful_life
                elif asset.depreciation_method == 'declining_balance':
                    asset.depreciation_rate = 200.0 / asset.useful_life
                elif asset.depreciation_method == 'double_declining':
                    asset.depreciation_rate = 400.0 / asset.useful_life
            else:
                asset.depreciation_rate = 0.0
    
    @api.depends('depreciation_line_ids', 'depreciation_line_ids.amount')
    def _compute_accumulated_depreciation(self):
        for asset in self:
            asset.accumulated_depreciation = sum(line.amount for line in asset.depreciation_line_ids.filtered(lambda l: l.state == 'posted'))
    
    @api.depends('purchase_value', 'accumulated_depreciation')
    def _compute_current_value(self):
        for asset in self:
            asset.current_value = asset.purchase_value - asset.accumulated_depreciation
    
    # Actions
    def action_confirm(self):
        if self.state != 'draft':
            raise UserError(_('Only draft assets can be confirmed.'))
        
        # Create first depreciation line
        self.env['custom_accounting.asset.depreciation.line'].create({
            'asset_id': self.id,
            'name': 'Initial Depreciation',
            'date': self.purchase_date,
            'amount': 0.0,  # First month might be partial
            'state': 'draft'
        })
        
        self.write({'state': 'running'})
    
    def action_compute_depreciation(self):
        self.ensure_one()
        
        if self.state != 'running':
            raise UserError(_('Only running assets can compute depreciation.'))
        
        # Calculate monthly depreciation
        depreciable_value = self.purchase_value - self.salvage_value
        
        if self.depreciation_method == 'straight_line':
            monthly_depreciation = depreciable_value / self.useful_life
        else:
            # Simplified calculation for declining balance methods
            monthly_rate = self.depreciation_rate / 12 / 100
            monthly_depreciation = self.current_value * monthly_rate
        
        # Create depreciation line for current month
        today = fields.Date.today()
        self.env['custom_accounting.asset.depreciation.line'].create({
            'asset_id': self.id,
            'name': 'Depreciation for %s' % today.strftime('%B %Y'),
            'date': today,
            'amount': monthly_depreciation,
            'state': 'draft'
        })
    
    def action_post_depreciation(self):
        self.ensure_one()
        
        # Post all draft depreciation lines
        draft_lines = self.depreciation_line_ids.filtered(lambda l: l.state == 'draft')
        
        for line in draft_lines:
            # Create journal entry for depreciation
            journal = self.env['custom_accounting.journal'].search([('type', '=', 'general')], limit=1)
            
            if not journal:
                raise UserError(_('No general journal found. Please create one first.'))
            
            # Create depreciation journal entry
            move = self.env['custom_accounting.move'].create({
                'name': 'Depreciation: %s' % self.name,
                'date': line.date,
                'journal_id': journal.id,
                'line_ids': [
                    (0, 0, {
                        'account_id': self.expense_account_id.id,
                        'name': 'Depreciation Expense: %s' % self.name,
                        'debit': line.amount,
                        'credit': 0.0,
                    }),
                    (0, 0, {
                        'account_id': self.depreciation_account_id.id,
                        'name': 'Accumulated Depreciation: %s' % self.name,
                        'debit': 0.0,
                        'credit': line.amount,
                    })
                ]
            })
            move.action_post()
            
            line.write({
                'state': 'posted',
                'move_id': move.id
            })
    
    # Constraints
    @api.constrains('purchase_value')
    def _check_purchase_value(self):
        for asset in self:
            if asset.purchase_value <= 0:
                raise ValidationError(_('Purchase value must be greater than zero.'))
    
    @api.constrains('useful_life')
    def _check_useful_life(self):
        for asset in self:
            if asset.useful_life <= 0:
                raise ValidationError(_('Useful life must be greater than zero.'))

class AssetCategory(models.Model):
    _name = 'custom_accounting.asset.category'
    _description = 'Asset Category'
    
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    
    # Default accounts
    default_asset_account_id = fields.Many2one('custom_accounting.account', string='Default Asset Account')
    default_depreciation_account_id = fields.Many2one('custom_accounting.account', string='Default Depreciation Account')
    default_expense_account_id = fields.Many2one('custom_accounting.account', string='Default Expense Account')
    
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Asset category code must be unique!'),
    ]

class AssetDepreciationLine(models.Model):
    _name = 'custom_accounting.asset.depreciation.line'
    _description = 'Asset Depreciation Line'
    _order = 'date desc'
    
    asset_id = fields.Many2one('custom_accounting.asset', string='Asset', required=True, ondelete='cascade')
    name = fields.Char(string='Description', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    amount = fields.Float(string='Amount', digits=(16, 2), required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted')
    ], string='Status', default='draft', required=True)
    
    # Link to journal entry
    move_id = fields.Many2one('custom_accounting.move', string='Journal Entry')
    
    def action_post(self):
        self.ensure_one()
        if self.state == 'draft':
            self.asset_id.action_post_depreciation()
