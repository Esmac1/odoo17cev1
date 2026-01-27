# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CustomMoveLine(models.Model):
    _name = 'custom_accounting.move.line'
    _description = 'Journal Item'
    _order = 'date desc, move_id desc, id desc'

    name = fields.Char(string='Label', required=True)
    date = fields.Date(string='Date', required=True, related='move_id.date', store=True)
    move_id = fields.Many2one('custom_accounting.move', string='Journal Entry', required=True, ondelete='cascade')

    account_id = fields.Many2one('custom_accounting.account', string='Account', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    debit = fields.Float(string='Debit', default=0.0)
    credit = fields.Float(string='Credit', default=0.0)
    balance = fields.Float(string='Balance', compute='_compute_balance', store=True)

    ref = fields.Char(string='Reference', related='move_id.ref', store=True)
    journal_id = fields.Many2one('custom_accounting.journal', string='Journal', related='move_id.journal_id', store=True)

    move_state = fields.Selection(string='Entry Status', related='move_id.state', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.depends('debit', 'credit')
    def _compute_balance(self):
        for line in self:
            line.balance = line.debit - line.credit

    @api.constrains('debit', 'credit')
    def _check_debit_credit(self):
        for line in self:
            if line.debit and line.credit:
                raise ValidationError("A journal item cannot have both debit and credit set!")
            if line.debit < 0 or line.credit < 0:
                raise ValidationError("Debit and credit amounts must be positive!")
