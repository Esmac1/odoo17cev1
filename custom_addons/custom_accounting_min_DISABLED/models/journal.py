# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CustomJournal(models.Model):
    _name = 'custom_accounting.journal'
    _description = 'Accounting Journal'

    name = fields.Char(string='Journal Name', required=True)
    code = fields.Char(string='Short Code', required=True, size=8)
    type = fields.Selection([
        ('sale', 'Sales'),
        ('purchase', 'Purchase'),
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('general', 'General'),
    ], string='Type', required=True, default='general')

    default_account_id = fields.Many2one('custom_accounting.account', string='Default Account')
    profit_account_id = fields.Many2one('custom_accounting.account', string='Profit Account')
    loss_account_id = fields.Many2one('custom_accounting.account', string='Loss Account')

    sequence_id = fields.Many2one('ir.sequence', string='Entry Sequence')
    refund_sequence_id = fields.Many2one('ir.sequence', string='Credit Note Sequence')

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        journal = super().create(vals)
        if not journal.sequence_id:
            seq = self.env['ir.sequence'].create({
                'name': f"{journal.name} Sequence",
                'code': f"custom_accounting.move.{journal.code}",
                'padding': 5,
                'company_id': journal.company_id.id,
            })
            journal.sequence_id = seq.id
        return journal
