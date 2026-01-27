# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class BankTransaction(models.Model):
    _name = 'custom_accounting.bank_transaction'
    _description = 'Bank Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference", required=True, default="New")
    date = fields.Date(default=fields.Date.today, required=True)
    partner_id = fields.Many2one('res.partner', string="Partner")
    amount = fields.Float(required=True)
    type = fields.Selection([
        ('deposit', 'Deposit / Receipt'),
        ('withdrawal', 'Withdrawal / Payment')
    ], required=True, default='deposit')

    account_id = fields.Many2one('custom_accounting.account', string='Bank Account', required=True,
                                 domain="[('type', 'in', ['asset']), ('reconcile', '=', True)]")
    journal_id = fields.Many2one('custom_accounting.journal', string='Journal', required=True)
    move_id = fields.Many2one('custom_accounting.move', string='Journal Entry', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('custom_accounting.bank_transaction') or 'New'
        return super().create(vals)

    def action_post(self):
        for rec in self:
            if rec.state != 'draft':
                continue

            # Determine debit/credit accounts
            if rec.type == 'deposit':
                debit_account = rec.account_id
                credit_account = rec.partner_id.property_account_receivable_id or self.env['custom_accounting.account'].search([('code', '=', '400001')], limit=1)  # fallback income
            else:
                debit_account = rec.partner_id.property_account_payable_id or self.env['custom_accounting.account'].search([('code', '=', '500001')], limit=1)
                credit_account = rec.account_id

            move_vals = {
                'date': rec.date,
                'journal_id': rec.journal_id.id,
                'ref': rec.name,
                'line_ids': [
                    (0, 0, {
                        'name': rec.name + " - Bank",
                        'account_id': rec.account_id.id,
                        'debit': rec.amount if rec.type == 'deposit' else 0,
                        'credit': rec.amount if rec.type == 'withdrawal' else 0,
                        'partner_id': rec.partner_id.id,
                    }),
                    (0, 0, {
                        'name': rec.name + " - Counterparty",
                        'account_id': credit_account.id if rec.type == 'deposit' else debit_account.id,
                        'debit': rec.amount if rec.type == 'withdrawal' else 0,
                        'credit': rec.amount if rec.type == 'deposit' else 0,
                        'partner_id': rec.partner_id.id,
                    }),
                ]
            }

            move = self.env['custom_accounting.move'].create(move_vals)
            move.action_post()
            rec.write({'move_id': move.id, 'state': 'posted'})

    def action_cancel(self):
        for rec in self:
            if rec.move_id:
                rec.move_id.button_cancel()
                rec.move_id.unlink()
            rec.state = 'cancelled'

    def action_reset_draft(self):
        self.write({'state': 'draft', 'move_id': False})
