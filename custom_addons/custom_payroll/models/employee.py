# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CustomPayrollEmployee(models.Model):
    _name = 'custom_payroll.employee'
    _description = 'Employee'
    _inherit = ['hr.employee']
    _order = 'name'
    
    # Additional fields for payroll
    payroll_number = fields.Char(string='Payroll Number', required=True, copy=False, default='New')
    employment_date = fields.Date(string='Employment Date', required=True)
    basic_salary = fields.Float(string='Basic Salary', required=True)
    housing_allowance = fields.Float(string='Housing Allowance', default=0)
    transport_allowance = fields.Float(string='Transport Allowance', default=0)
    medical_allowance = fields.Float(string='Medical Allowance', default=0)
    
    # Nigerian-specific fields
    kra_pin = fields.Char(string='KRA PIN')
    nssf_number = fields.Char(string='NSSF Number')
    nhif_number = fields.Char(string='NHIF Number')
    
    # Status
    payroll_active = fields.Boolean(string='Active in Payroll', default=True)
    
    # Relations
    contract_ids = fields.One2many('custom_payroll.contract', 'employee_id', string='Contracts')
    active_contract_id = fields.Many2one('custom_payroll.contract', string='Active Contract',
                                        compute='_compute_active_contract', store=True)
    payslip_ids = fields.One2many('custom_payroll.payslip', 'employee_id', string='Payslips')
    loan_ids = fields.One2many('custom_payroll.loan', 'employee_id', string='Loans')
    work_entry_ids = fields.One2many('custom_payroll.work_entry', 'employee_id', string='Work Entries')
    
    # Computed fields
    total_earnings = fields.Float(string='Total Earnings', compute='_compute_totals', store=True)
    total_deductions = fields.Float(string='Total Deductions', compute='_compute_totals', store=True)
    net_salary = fields.Float(string='Net Salary', compute='_compute_totals', store=True)
    
    _sql_constraints = [
        ('payroll_number_uniq', 'unique(payroll_number)', 'Payroll Number must be unique!'),
    ]
    
    @api.depends('basic_salary', 'housing_allowance', 'transport_allowance', 'medical_allowance')
    def _compute_totals(self):
        for employee in self:
            employee.total_earnings = employee.basic_salary + employee.housing_allowance + \
                                      employee.transport_allowance + employee.medical_allowance
            # Deductions would be computed from payslips
            employee.total_deductions = 0  # Will be computed from actual deductions
            employee.net_salary = employee.total_earnings - employee.total_deductions
    
    @api.depends('contract_ids', 'contract_ids.state')
    def _compute_active_contract(self):
        for employee in self:
            active_contract = employee.contract_ids.filtered(lambda c: c.state == 'active')
            employee.active_contract_id = active_contract[0] if active_contract else False
    
    @api.model
    def create(self, vals):
        if vals.get('payroll_number', 'New') == 'New':
            vals['payroll_number'] = self.env['ir.sequence'].next_by_code('custom_payroll.employee') or 'New'
        return super().create(vals)
    
    def action_view_contracts(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contracts',
            'res_model': 'custom_payroll.contract',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {'default_employee_id': self.id},
        }
    
    def action_view_payslips(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payslips',
            'res_model': 'custom_payroll.payslip',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
        }
