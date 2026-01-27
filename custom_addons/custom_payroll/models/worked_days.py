# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CustomPayrollWorkedDays(models.Model):
    _name = 'custom_payroll.worked_days'
    _description = 'Worked Days'
    
    payslip_id = fields.Many2one('custom_payroll.payslip', string='Payslip', required=True, ondelete='cascade')
    employee_id = fields.Many2one('custom_payroll.employee', string='Employee', related='payslip_id.employee_id', store=True)
    name = fields.Char(string='Description', required=True)
    code = fields.Selection([
        ('WORK100', 'Normal Working Days'),
        ('WORK50', 'Half Working Days'),
        ('OVERTIME', 'Overtime'),
        ('HOLIDAY', 'Public Holiday'),
        ('WEEKEND', 'Weekend Work'),
    ], string='Work Code', required=True)
    number_of_days = fields.Float(string='Number of Days', required=True, default=0)
    number_of_hours = fields.Float(string='Number of Hours', default=0)
    hourly_rate = fields.Float(string='Hourly Rate', compute='_compute_rates', store=True)
    daily_rate = fields.Float(string='Daily Rate', compute='_compute_rates', store=True)
    amount = fields.Float(string='Amount', compute='_compute_amount', store=True)
    date_from = fields.Date(string='From Date', related='payslip_id.date_from', store=True)
    date_to = fields.Date(string='To Date', related='payslip_id.date_to', store=True)
    
    @api.depends('employee_id', 'payslip_id.contract_id')
    def _compute_rates(self):
        for line in self:
            contract = line.payslip_id.contract_id
            if contract and contract.wage_type == 'monthly':
                line.daily_rate = contract.wage / 22
                line.hourly_rate = contract.hourly_wage
            else:
                line.daily_rate = 0
                line.hourly_rate = 0
    
    @api.depends('number_of_days', 'number_of_hours', 'daily_rate', 'hourly_rate', 'code')
    def _compute_amount(self):
        for line in self:
            if line.code == 'OVERTIME':
                line.amount = line.number_of_hours * line.hourly_rate * 1.5
            elif line.code == 'HOLIDAY' or line.code == 'WEEKEND':
                line.amount = line.number_of_days * line.daily_rate * 2
            else:
                if line.number_of_hours > 0:
                    line.amount = line.number_of_hours * line.hourly_rate
                else:
                    line.amount = line.number_of_days * line.daily_rate
