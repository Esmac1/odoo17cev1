# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CustomAsset(models.Model):
    _name = 'custom_accounting.asset'
    _description = 'Custom Accounting Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Asset Name", required=True, tracking=True)
    acquisition_date = fields.Date(string="Acquisition Date", default=fields.Date.today)
    value = fields.Float(string="Asset Value", required=True)
    depreciation_rate = fields.Float(string="Depreciation Rate (%)", default=10.0)
    accumulated_depreciation = fields.Float(
        string="Accumulated Depreciation", compute="_compute_accumulated", store=True)
    residual_value = fields.Float(
        string="Residual Value", compute="_compute_residual", store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('closed', 'Closed'),
    ], string="Status", default='draft', tracking=True)

    account_id = fields.Many2one('custom_accounting.account', string='Asset Account')
    journal_id = fields.Many2one('custom_accounting.journal', string='Journal')

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one(
        'res.users', string='Responsible', default=lambda self: self.env.user)

    @api.depends('value', 'depreciation_rate')
    def _compute_accumulated(self):
        for rec in self:
            rec.accumulated_depreciation = rec.value * (rec.depreciation_rate / 100.0)

    @api.depends('value', 'accumulated_depreciation')
    def _compute_residual(self):
        for rec in self:
            rec.residual_value = rec.value - rec.accumulated_depreciation

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        account = self.env['custom_accounting.account'].search(
            [('account_type', '=', 'asset')], limit=1)
        if account:
            res['account_id'] = account.id
        return res

    def action_start(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError("Asset can only start from Draft state.")
            rec.state = 'running'

    def action_close(self):
        for rec in self:
            if rec.state != 'running':
                raise ValidationError("Only running assets can be closed.")
            rec.state = 'closed'

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def _cron_generate_depreciation_entries(self):
        """Automatically generate monthly depreciation journal entries."""
        journal = self.env['custom_accounting.journal'].search(
            [('type', '=', 'general')], limit=1)
        expense_account = self.env['custom_accounting.account'].search(
            [('code', '=', '900003')], limit=1)  # General Expense
        for asset in self.search([('state', '=', 'running')]):
            if not journal or not asset.account_id or not expense_account:
                continue

            amount = asset.value * (asset.depreciation_rate / 100.0)
            move_vals = {
                'date': fields.Date.today(),
                'journal_id': journal.id,
                'ref': f"Depreciation - {asset.name}",
                'line_ids': [
                    (0, 0, {
                        'name': f"Depreciation Expense - {asset.name}",
                        'account_id': expense_account.id,
                        'debit': amount,
                    }),
                    (0, 0, {
                        'name': f"Accumulated Depreciation - {asset.name}",
                        'account_id': asset.account_id.id,
                        'credit': amount,
                    }),
                ],
            }
            self.env['custom_accounting.move'].create(move_vals).action_post()
