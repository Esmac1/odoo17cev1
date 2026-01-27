# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _description = 'Purchase Order Extension'

    custom_reference = fields.Char(string="Custom Reference")
    approval_date = fields.Date(string="Approval Date")
    approved_by = fields.Many2one('res.users', string="Approved By")
    accounting_note = fields.Text(string="Accounting Note")

    def button_approve(self, force=False):
        res = super().button_approve(force=force)
        self.write({
            'approval_date': fields.Date.today(),
            'approved_by': self.env.user.id,
        })
        return res
