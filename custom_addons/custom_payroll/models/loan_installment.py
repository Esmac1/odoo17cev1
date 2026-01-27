# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CustomPayrollLoanInstallment(models.Model):
    _name = 'custom_payroll.loan_installment'
    _description = 'Loan Installment'
    _order = 'sequence'
    
    loan_id = fields.Many2one('custom_payroll.loan', string='Loan', required=True, ondelete='cascade')
    employee_id = fields.Many2one('custom_payroll.employee', string='Employee', related='loan_id.employee_id', store=True)
    sequence = fields.Integer(string='Installment #', required=True)
    due_date = fields.Date(string='Due Date', required=True)
    amount = fields.Float(string='Amount', required=True)
    principal = fields.Float(string='Principal')
    interest = fields.Float(string='Interest')
    state = fields.Selection([
        ('due', 'Due'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='due')
    payment_date = fields.Date(string='Payment Date')
    payslip_id = fields.Many2one('custom_payroll.payslip', string='Deducted From Payslip')
    company_id = fields.Many2one('res.company', string='Company', related='loan_id.company_id', store=True)
    days_overdue = fields.Integer(string='Days Overdue', compute='_compute_overdue')
    late_fee = fields.Float(string='Late Fee', default=0)
    
    @api.depends('due_date', 'state')
    def _compute_overdue(self):
        today = fields.Date.today()
        for installment in self:
            if installment.state == 'due' and installment.due_date:
                if installment.due_date < today:
                    delta = today - installment.due_date
                    installment.days_overdue = delta.days
                    installment.state = 'overdue'
                else:
                    installment.days_overdue = 0
            else:
                installment.days_overdue = 0
    
    def action_mark_as_paid(self):
        self.write({
            'state': 'paid',
            'payment_date': fields.Date.today(),
        })
