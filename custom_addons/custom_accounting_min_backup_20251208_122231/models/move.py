# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class CustomMove(models.Model):
    _name = 'custom_accounting.move'
    _description = 'Accounting Entry'
    _order = 'date desc, name desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Number', required=True, copy=False, readonly=True, default='/')
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    ref = fields.Char(string='Reference')

    journal_id = fields.Many2one('custom_accounting.journal', string='Journal', required=True)
    line_ids = fields.One2many('custom_accounting.move.line', 'move_id', string='Journal Items')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    amount_total = fields.Float(string='Total', compute='_compute_amounts', store=True)
    balance_check = fields.Float(string='Balance Check', compute='_compute_amounts', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.depends('line_ids.debit', 'line_ids.credit')
    def _compute_amounts(self):
        for move in self:
            total_debit = sum(move.line_ids.mapped('debit'))
            total_credit = sum(move.line_ids.mapped('credit'))
            move.amount_total = max(total_debit, total_credit)
            move.balance_check = total_debit - total_credit

    @api.constrains('line_ids')
    def _check_balanced(self):
        for move in self:
            if move.line_ids and abs(move.balance_check) > 0.01:
                raise ValidationError("Journal entry must be balanced! Debit and credit totals must match.")

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals.get('name') == '/':
            journal = self.env['custom_accounting.journal'].browse(vals.get('journal_id'))
            if journal and journal.sequence_id:
                vals['name'] = journal.sequence_id.next_by_id()
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('custom_accounting.move')
        return super().create(vals)

    def unlink(self):
        for move in self:
            if move.state == 'posted':
                raise UserError("You cannot delete a posted journal entry!")
        return super().unlink()

    def action_post(self):
        for move in self:
            if move.state != 'draft':
                raise UserError("Only draft entries can be posted.")
            if abs(move.balance_check) > 0.01:
                raise UserError("Cannot post unbalanced journal entry!")
            move.state = 'posted'

    def action_draft(self):
        for move in self:
            if move.state not in ('posted', 'cancel'):
                raise UserError("Only posted or cancelled entries can be reset to draft.")
            move.state = 'draft'

    def action_cancel(self):
        for move in self:
            if move.state != 'posted':
                raise UserError("Only posted journal entries can be cancelled.")
            move.state = 'cancel'
