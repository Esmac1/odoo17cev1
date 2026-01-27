# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CustomPayrollPayslipLine(models.Model):
    _name = 'custom_payroll.payslip_line'
    _description = 'Payslip Line'
    _order = 'sequence, id'
    
    slip_id = fields.Many2one('custom_payroll.payslip', string='Payslip', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Description', required=True)
    code = fields.Char(string='Code', required=True)
    category = fields.Selection([
        ('allowance', 'Allowance'),
        ('deduction', 'Deduction'),
        ('total', 'Total'),
        ('other', 'Other'),
    ], string='Category', default='other')
    amount = fields.Float(string='Amount', required=True)
    rate = fields.Float(string='Rate (%)', default=100)
    quantity = fields.Float(string='Quantity', default=1)
    total = fields.Float(string='Total', compute='_compute_total', store=True)
    salary_rule_id = fields.Many2one('custom_payroll.salary_rule', string='Salary Rule')
    account_debit = fields.Many2one('custom_accounting.account', string='Debit Account')
    account_credit = fields.Many2one('custom_accounting.account', string='Credit Account')
    
    @api.depends('amount', 'rate', 'quantity')
    def _compute_total(self):
        for line in self:
            line.total = line.amount * (line.rate / 100) * line.quantity
