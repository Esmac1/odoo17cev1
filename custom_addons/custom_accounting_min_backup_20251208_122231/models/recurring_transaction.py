# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta


class RecurringTransaction(models.Model):
    _name = 'custom_accounting.recurring'
    _description = 'Recurring Transaction'

    name = fields.Char(required=True)
    partner_id = fields.Many2one('res.partner', string="Partner")
    amount = fields.Float(required=True)
    interval_number = fields.Integer(string="Repeat every", default=1)
    interval_type = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
    ], default='months')
    next_date = fields.Date(default=fields.Date.today)
    journal_id = fields.Many2one('custom_accounting.journal', string='Journal', required=True)
    account_id = fields.Many2one('custom_accounting.account', string='Account', required=True)
    active = fields.Boolean(default=True)
    move_ids = fields.One2many('custom_accounting.move', 'ref', string='Generated Entries')

    def action_generate_entries(self):
        """Manually trigger or via cron."""
        today = fields.Date.today()
        for rec in self.filtered(lambda r: r.active and r.next_date <= today):
            move_vals = {
                'date': today,
                'journal_id': rec.journal_id.id,
                'ref': f"Recurring - {rec.name}",
                'line_ids': [
                    (0, 0, {
                        'name': rec.name,
                        'account_id': rec.account_id.id,
                        'debit': rec.amount if rec.amount > 0 else 0,
                        'credit': -rec.amount if rec.amount < 0 else 0,
                    }),
                    (0, 0, {
                        'name': rec.name,
                        'account_id': rec.account_id.id,
                        'debit': -rec.amount if rec.amount < 0 else 0,
                        'credit': rec.amount if rec.amount > 0 else 0,
                    }),
                ]
            }
            self.env['custom_accounting.move'].create(move_vals)

            # Schedule next
            if rec.interval_type == 'days':
                delta = timedelta(days=rec.interval_number)
            elif rec.interval_type == 'weeks':
                delta = timedelta(weeks=rec.interval_number)
            else:
                delta = timedelta(days=30 * rec.interval_number)
            rec.next_date = rec.next_date + delta

    def _cron_generate_recurring_entries(self):
        """Can be tied to ir.cron for automation."""
        self.search([('active', '=', True)]).action_generate_entries()
