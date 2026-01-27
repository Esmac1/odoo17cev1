# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date

class Reconciliation(models.Model):
    _name = 'custom_accounting.reconciliation'
    _description = 'Bank Reconciliation'
    _order = 'date desc, id desc'
    
    name = fields.Char(string='Reference', required=True, default=lambda self: self.env['ir.sequence'].next_by_code('custom_accounting.reconciliation'))
    date = fields.Date(string='Reconciliation Date', required=True, default=fields.Date.today)
    bank_account_id = fields.Many2one('custom_accounting.account', string='Bank Account', 
                                      required=True, domain=[('type', '=', 'bank')])
    statement_date = fields.Date(string='Statement Date', required=True)
    statement_balance = fields.Float(string='Statement Balance', required=True)
    reconciled_balance = fields.Float(string='Reconciled Balance', compute='_compute_reconciled_balance', store=True)
    difference = fields.Float(string='Difference', compute='_compute_difference', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True)
    
    # Lines
    line_ids = fields.One2many('custom_accounting.reconciliation.line', 'reconciliation_id', string='Reconciliation Lines')
    move_line_ids = fields.One2many('custom_accounting.move.line', compute='_compute_move_lines', string='Unreconciled Move Lines')
    
    # Computed fields
    @api.depends('line_ids', 'line_ids.amount', 'line_ids.is_reconciled')
    def _compute_reconciled_balance(self):
        for rec in self:
            reconciled_amount = sum(line.amount for line in rec.line_ids.filtered(lambda l: l.is_reconciled))
            rec.reconciled_balance = reconciled_amount
    
    @api.depends('statement_balance', 'reconciled_balance')
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.statement_balance - rec.reconciled_balance
    
    @api.depends('bank_account_id', 'date')
    def _compute_move_lines(self):
        for rec in self:
            if rec.bank_account_id:
                move_lines = self.env['custom_accounting.move.line'].search([
                    ('account_id', '=', rec.bank_account_id.id),
                    ('reconciled', '=', False),
                    ('move_id.state', '=', 'posted'),
                    ('date', '<=', rec.date)
                ])
                rec.move_line_ids = move_lines
            else:
                rec.move_line_ids = False
    
    # Actions
    def action_start_reconciliation(self):
        self.write({'state': 'in_progress'})
    
    def action_complete_reconciliation(self):
        if abs(self.difference) > 0.01:
            raise UserError(_('Reconciliation cannot be completed. Difference must be zero.'))
        
        # Mark lines as reconciled
        for line in self.line_ids.filtered(lambda l: l.is_reconciled):
            if line.move_line_id:
                line.move_line_id.write({'reconciled': True})
        
        self.write({'state': 'completed'})
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})
    
    def action_reset_draft(self):
        self.write({'state': 'draft'})
    
    # Constraints
    @api.constrains('statement_balance')
    def _check_statement_balance(self):
        for rec in self:
            if rec.statement_balance < 0:
                raise ValidationError(_('Statement balance cannot be negative.'))

class ReconciliationLine(models.Model):
    _name = 'custom_accounting.reconciliation.line'
    _description = 'Bank Reconciliation Line'
    
    reconciliation_id = fields.Many2one('custom_accounting.reconciliation', string='Reconciliation', required=True, ondelete='cascade')
    move_line_id = fields.Many2one('custom_accounting.move.line', string='Journal Item', required=True)
    date = fields.Date(string='Date', related='move_line_id.date', store=True)
    description = fields.Char(string='Description', related='move_line_id.name', store=True)
    
    # Calculate amount based on debit/credit
    amount = fields.Float(string='Amount', compute='_compute_amount', store=True)
    
    is_reconciled = fields.Boolean(string='Reconciled', default=True)
    
    @api.depends('move_line_id', 'move_line_id.debit', 'move_line_id.credit')
    def _compute_amount(self):
        for line in self:
            if line.move_line_id:
                # For bank accounts, debit increases balance, credit decreases balance
                # So amount = debit - credit
                line.amount = line.move_line_id.balance
            else:
                line.amount = 0.0
    
    # Constraints
    @api.constrains('move_line_id')
    def _check_move_line_uniqueness(self):
        for line in self:
            existing = self.search([
                ('move_line_id', '=', line.move_line_id.id),
                ('reconciliation_id', '!=', line.reconciliation_id.id),
                ('reconciliation_id.state', 'in', ['draft', 'in_progress'])
            ])
            if existing:
                raise ValidationError(_('This journal item is already being reconciled in another reconciliation.'))
