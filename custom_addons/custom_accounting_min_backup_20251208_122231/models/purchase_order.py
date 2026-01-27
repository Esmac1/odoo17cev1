from odoo import models, fields


class PurchaseOrderExtension(models.Model):
    _inherit = 'purchase.order'

    custom_reference = fields.Char(string="Custom Ref")
    approval_date = fields.Date(string="Approval Date")
    approved_by = fields.Many2one('res.users', string="Approved By")
