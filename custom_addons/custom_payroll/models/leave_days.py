# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CustomPayrollLeaveDays(models.Model):
    _name = 'custom_payroll.leave_days'
    _description = 'Leave Days'
    
    payslip_id = fields.Many2one('custom_payroll.payslip', string='Payslip', required=True, ondelete='cascade')
    employee_id = fields.Many2one('custom_payroll.employee', string='Employee', related='payslip_id.employee_id', store=True)
    name = fields.Char(string='Description', required=True)
    code = fields.Selection([
        ('ANNUAL', 'Annual Leave'),
        ('SICK', 'Sick Leave'),
        ('MATERNITY', 'Maternity Leave'),
        ('PATERNITY', 'Paternity Leave'),
        ('UNPAID', 'Unpaid Leave'),
        ('OTHER', 'Other Leave'),
    ], string='Leave Code', required=True)
    number_of_days = fields.Float(string='Number of Days', required=True, default=0)
    paid = fields.Boolean(string='Paid Leave', default=True)
    amount = fields.Float(string='Amount', compute='_compute_amount', store=True)
    
    @api.depends('number_of_days', 'paid', 'payslip_id.contract_id')
    def _compute_amount(self):
        for line in self:
            if line.paid:
                contract = line.payslip_id.contract_id
                if contract:
                    daily_rate = contract.wage / 22
                    line.amount = line.number_of_days * daily_rate
                else:
                    line.amount = 0
            else:
                line.amount = 0
