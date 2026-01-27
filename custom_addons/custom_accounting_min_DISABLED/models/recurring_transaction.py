# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime

class RecurringTransaction(models.Model):
    _name = 'custom_accounting.recurring'
    _description = 'Recurring Transaction Template'
    _order = 'next_date, name'
    
    # Basic Information
    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    
    # Scheduling
    journal_id = fields.Many2one('custom_accounting.journal', string='Journal', required=True)
    interval_number = fields.Integer(string='Interval', default=1, required=True)
    interval_type = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ], string='Interval Unit', default='months', required=True)
    
    # Execution
    next_date = fields.Date(string='Next Execution Date', required=True, default=fields.Date.today)
    last_executed = fields.Date(string='Last Executed')
    total_executions = fields.Integer(string='Total Executions', default=0)
    max_executions = fields.Integer(string='Maximum Executions', default=0)  # 0 = unlimited
    
    # Lines
    line_ids = fields.One2many('custom_accounting.recurring.line', 'recurring_id', string='Transaction Lines')
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('paused', 'Paused'),
        ('completed', 'Completed')
    ], string='Status', default='draft', required=True)
    
    # Computed fields
    @api.depends('line_ids', 'line_ids.debit', 'line_ids.credit')
    def _compute_total_amount(self):
        for rec in self:
            total_debit = sum(line.debit for line in rec.line_ids)
            total_credit = sum(line.credit for line in rec.line_ids)
            rec.total_debit = total_debit
            rec.total_credit = total_credit
    
    total_debit = fields.Float(string='Total Debit', compute='_compute_total_amount', store=True)
    total_credit = fields.Float(string='Total Credit', compute='_compute_total_amount', store=True)
    
    # Constraints
    @api.constrains('interval_number')
    def _check_interval_number(self):
        for rec in self:
            if rec.interval_number <= 0:
                raise ValidationError(_('Interval must be greater than zero.'))
    
    @api.constrains('line_ids')
    def _check_lines_balance(self):
        for rec in self:
            if abs(rec.total_debit - rec.total_credit) > 0.01:
                raise ValidationError(_('Debit and credit totals must be equal.'))
    
    # Actions
    def action_activate(self):
        self.write({'state': 'running', 'active': True})
    
    def action_pause(self):
        self.write({'state': 'paused'})
    
    def action_complete(self):
        self.write({'state': 'completed', 'active': False})
    
    def action_generate_entries(self):
        """Generate journal entries for all due recurring transactions"""
        due_transactions = self.search([
            ('state', '=', 'running'),
            ('active', '=', True),
            ('next_date', '<=', fields.Date.today())
        ])
        
        generated_moves = []
        for transaction in due_transactions:
            moves = transaction._generate_journal_entry()
            generated_moves.extend(moves)
            
            # Update transaction
            transaction.last_executed = fields.Date.today()
            transaction.total_executions += 1
            
            # Calculate next date
            if transaction.interval_type == 'days':
                delta = relativedelta(days=transaction.interval_number)
            elif transaction.interval_type == 'weeks':
                delta = relativedelta(weeks=transaction.interval_number)
            elif transaction.interval_type == 'months':
                delta = relativedelta(months=transaction.interval_number)
            else:  # years
                delta = relativedelta(years=transaction.interval_number)
            
            transaction.next_date = transaction.next_date + delta
            
            # Check if max executions reached
            if transaction.max_executions > 0 and transaction.total_executions >= transaction.max_executions:
                transaction.action_complete()
        
        # Return action to view generated moves
        if generated_moves:
            return {
                'name': _('Generated Journal Entries'),
                'type': 'ir.actions.act_window',
                'res_model': 'custom_accounting.move',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', generated_moves)],
                'context': {'create': False},
            }
        else:
            raise UserError(_('No recurring transactions were due for execution.'))
    
    def _generate_journal_entry(self):
        """Generate a single journal entry for this recurring transaction"""
        self.ensure_one()
        
        # Create move lines
        move_lines = []
        for line in self.line_ids:
            move_lines.append((0, 0, {
                'account_id': line.account_id.id,
                'name': line.name,
                'debit': line.debit,
                'credit': line.credit,
            }))
        
        # Create journal entry
        move = self.env['custom_accounting.move'].create({
            'name': 'Recurring: %s' % self.name,
            'date': self.next_date,
            'journal_id': self.journal_id.id,
            'ref': self.description or self.name,
            'line_ids': move_lines,
        })
        
        # Post the move
        move.action_post()
        
        return [move.id]
    
    @api.model
    def cron_generate_recurring_entries(self):
        """Cron job to automatically generate recurring entries"""
        self.action_generate_entries()

class RecurringLine(models.Model):
    _name = 'custom_accounting.recurring.line'
    _description = 'Recurring Transaction Line'
    
    recurring_id = fields.Many2one('custom_accounting.recurring', string='Recurring Transaction', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    
    name = fields.Char(string='Description', required=True)
    account_id = fields.Many2one('custom_accounting.account', string='Account', required=True)
    debit = fields.Float(string='Debit', default=0.0, digits=(16, 2))
    credit = fields.Float(string='Credit', default=0.0, digits=(16, 2))
    
    # Partner information (optional)
    partner_id = fields.Many2one('res.partner', string='Partner')
    
    # Analytic accounting (optional)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    
    _order = 'sequence, id'
