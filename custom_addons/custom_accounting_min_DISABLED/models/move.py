# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class CustomMove(models.Model):
    _name = 'custom_accounting.move'
    _description = 'Journal Entry'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ========== BASIC FIELDS ==========
    name = fields.Char(string='Number', readonly=True, index=True, 
                      default=lambda self: self.env['ir.sequence'].next_by_code('custom_accounting.move'))
    date = fields.Date(string='Date', required=True, default=fields.Date.today, index=True,
                      tracking=True)
    ref = fields.Char(string='Reference', tracking=True)
    
    # ========== JOURNAL ==========
    journal_id = fields.Many2one('custom_accounting.journal', string='Journal', 
                                required=True, index=True, tracking=True)
    
    # ========== MULTI-CURRENCY ==========
    currency_id = fields.Many2one('res.currency', string='Currency',
                                 compute='_compute_currency', store=True)
    has_foreign_currency = fields.Boolean(string='Has Foreign Currency', 
                                         compute='_compute_has_foreign_currency', store=True)
    
    # ========== AMOUNTS ==========
    amount = fields.Float(string='Total Amount', compute='_compute_amount', store=True, digits=(16, 2))
    amount_foreign = fields.Float(string='Total in Foreign', compute='_compute_amount_foreign', digits=(16, 2))
    
    # ========== LINES ==========
    line_ids = fields.One2many('custom_accounting.move.line', 'move_id', string='Journal Items')
    
    # ========== STATE ==========
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True, index=True)
    
    # ========== COMPANY ==========
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True, index=True)
    
    # ========== COMPUTED FIELDS ==========
    @api.depends('line_ids.account_id.currency_id')
    def _compute_currency(self):
        for move in self:
            currencies = move.line_ids.mapped('account_id.currency_id')
            if len(currencies) == 1:
                move.currency_id = currencies[0]
            else:
                move.currency_id = self.env.company.currency_id
    
    @api.depends('line_ids.account_id.currency_id')
    def _compute_has_foreign_currency(self):
        for move in self:
            move.has_foreign_currency = any(
                line.account_id.currency_id and 
                line.account_id.currency_id != self.env.company.currency_id 
                for line in move.line_ids
            )
    
    @api.depends('line_ids.debit', 'line_ids.credit')
    def _compute_amount(self):
        for move in self:
            total_debit = sum(move.line_ids.mapped('debit'))
            total_credit = sum(move.line_ids.mapped('credit'))
            move.amount = max(total_debit, total_credit)
    
    @api.depends('line_ids.amount_currency')
    def _compute_amount_foreign(self):
        for move in self:
            move.amount_foreign = sum(abs(line.amount_currency) for line in move.line_ids)
    
    # ========== CONSTRAINTS ==========
    @api.constrains('line_ids')
    def _check_balanced(self):
        for move in self:
            if abs(sum(move.line_ids.mapped('debit')) - sum(move.line_ids.mapped('credit'))) > 0.01:
                raise ValidationError(_('Journal entry must be balanced (debit = credit).'))
    
    @api.constrains('line_ids')
    def _check_currency_consistency(self):
        for move in self:
            for line in move.line_ids:
                if line.account_id.currency_id and line.amount_currency == 0:
                    raise ValidationError(
                        _('Line %s: Amount in currency is required for foreign currency accounts.')
                        % line.name
                    )
    
    # ========== ACTION METHODS ==========
    def action_post(self):
        for move in self:
            if move.state != 'draft':
                raise UserError(_('Only draft entries can be posted.'))
            
            # Validate foreign currency amounts
            for line in move.line_ids:
                if line.account_id.currency_id:
                    # Auto-calculate exchange rate if not set
                    if not line.exchange_rate and line.amount_currency != 0:
                        company_currency = self.env.company.currency_id
                        if line.account_id.currency_id != company_currency:
                            # Get latest exchange rate
                            rate = self.env['custom_accounting.currency.rate'].get_rate(
                                line.account_id.currency_id.id,
                                move.date
                            )
                            line.exchange_rate = rate
            
            move.write({'state': 'posted'})
        return True
    
    def action_cancel(self):
        for move in self:
            if move.state == 'posted':
                # Check if any lines are reconciled
                reconciled_lines = move.line_ids.filtered(lambda l: l.reconciled)
                if reconciled_lines:
                    raise UserError(_(
                        'Cannot cancel a journal entry with reconciled lines. '
                        'Lines: %s'
                    ) % ', '.join(reconciled_lines.mapped('name')))
            
            move.write({'state': 'cancelled'})
        return True
    
    def action_draft(self):
        self.write({'state': 'draft'})
        return True
    
    # ========== HELPER METHODS ==========
    def auto_compute_currency_amounts(self):
        """Auto-compute amount_currency based on debit/credit and exchange rate"""
        for move in self:
            for line in move.line_ids:
                if line.account_id.currency_id and line.exchange_rate and line.exchange_rate > 0:
                    if line.debit > 0:
                        line.amount_currency = line.debit / line.exchange_rate
                    elif line.credit > 0:
                        line.amount_currency = -line.credit / line.exchange_rate
