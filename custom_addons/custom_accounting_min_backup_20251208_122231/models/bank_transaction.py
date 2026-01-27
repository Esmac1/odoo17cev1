# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BankTransaction(models.Model):
    _name = 'custom_accounting.bank_transaction'
    _description = 'Bank Transaction'

    name = fields.Char(string="Reference", required=True)
    date = fields.Date(default=fields.Date.today)
    partner_id = fields.Many2one('res.partner', string="Partner")
    amount = fields.Float(required=True)
    type = fields.Selection([
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal')
    ], default='deposit', required=True)

    account_id = fields.Many2one('custom_accounting.account', string='Bank Account', required=True)
    journal_id = fields.Many2one('custom_accounting.journal', string='Journal', required=True)
    move_id = fields.Many2one('custom_accounting.move', string='Journal Entry', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ], default='draft', string="Status", tracking=True)

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("Amount must be greater than zero.")

    def action_post(self):
        """Generate a journal entry for this transaction."""
        for rec in self:
            if rec.state != 'draft':
                continue
            move_vals = {
                'date': rec.date,
                'journal_id': rec.journal_id.id,
                'ref': rec.name,
                'line_ids': [],
            }

            if rec.type == 'deposit':
                move_vals['line_ids'] = [
                    (0, 0, {'name': rec.name, 'account_id': rec.account_id.id, 'debit': rec.amount}),
                    (0, 0, {'name': rec.name, 'account_id': rec.account_id.id, 'credit': rec.amount}),
                ]
            else:
                move_vals['line_ids'] = [
                    (0, 0, {'name': rec.name, 'account_id': rec.account_id.id, 'credit': rec.amount}),
                    (0, 0, {'name': rec.name, 'account_id': rec.account_id.id, 'debit': rec.amount}),
                ]

            move = self.env['custom_accounting.move'].create(move_vals)
            rec.move_id = move.id
            rec.state = 'posted'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'
