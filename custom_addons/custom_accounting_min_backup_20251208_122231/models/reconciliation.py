# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Reconciliation(models.Model):
    _name = 'custom_accounting.reconcile'
    _description = 'Account Reconciliation'

    name = fields.Char(string="Reconciliation Ref", required=True)
    account_id = fields.Many2one('custom_accounting.account', string="Account", required=True)
    transaction_ids = fields.Many2many(
        'custom_accounting.bank_transaction',
        'custom_reconcile_banktxn_rel',
        'reconcile_id',
        'bank_transaction_id',
        string="Transactions"
    )
    balance_system = fields.Float(string="System Balance")
    balance_bank = fields.Float(string="Bank Statement Balance")
    difference = fields.Float(string="Difference", compute="_compute_difference", store=True)
    reconciled = fields.Boolean(string="Reconciled", compute="_compute_reconciled", store=True)

    @api.depends('balance_system', 'balance_bank')
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.balance_bank - rec.balance_system

    @api.depends('difference')
    def _compute_reconciled(self):
        for rec in self:
            rec.reconciled = abs(rec.difference) < 0.01

    def action_reconcile(self):
        for rec in self:
            rec.balance_system = sum(
                rec.transaction_ids.filtered(lambda t: t.state == 'posted').mapped('amount'))
            rec._compute_difference()
