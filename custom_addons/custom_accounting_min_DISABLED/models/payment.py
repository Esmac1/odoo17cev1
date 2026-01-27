# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CustomPayment(models.Model):
    _name = 'custom_accounting.payment'
    _description = 'Customer / Vendor Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name desc'

    name = fields.Char(string='Number', default='New', copy=False)
    date = fields.Date(required=True, default=fields.Date.today)
    amount = fields.Float(required=True)
    payment_type = fields.Selection([
        ('inbound', 'Customer Payment'),
        ('outbound', 'Vendor Payment')
    ], required=True, default='inbound')
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    journal_id = fields.Many2one('custom_accounting.journal', string='Journal', required=True)
    account_id = fields.Many2one('custom_accounting.account', string='Bank/Cash Account', required=True)
    
    # CHANGE FROM Many2many TO Many2one:
    invoice_id = fields.Many2one('custom_accounting.invoice', string='Invoice', ondelete='set null')
    
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
            seq = 'custom_accounting.payment.in' if vals.get('payment_type') == 'inbound' else 'custom_accounting.payment.out'
            vals['name'] = self.env['ir.sequence'].next_by_code(seq) or 'New'
        return super().create(vals)

    def action_post(self):
        for pay in self:
            if pay.state != 'draft':
                continue
            counter_account = pay.partner_id.property_account_receivable_id if pay.payment_type == 'inbound' else pay.partner_id.property_account_payable_id
            lines = [
                (0, 0, {'name': pay.name, 'account_id': pay.account_id.id,
                        'debit': pay.amount if pay.payment_type == 'inbound' else 0,
                        'credit': pay.amount if pay.payment_type == 'outbound' else 0,
                        'partner_id': pay.partner_id.id}),
                (0, 0, {'name': pay.name, 'account_id': counter_account.id,
                        'debit': pay.amount if pay.payment_type == 'outbound' else 0,
                        'credit': pay.amount if pay.payment_type == 'inbound' else 0,
                        'partner_id': pay.partner_id.id}),
            ]
            move = self.env['custom_accounting.move'].create({
                'date': pay.date,
                'journal_id': pay.journal_id.id,
                'ref': pay.name,
                'line_ids': lines,
            })
            move.action_post()
            pay.move_id = move.id
            pay.state = 'posted'
