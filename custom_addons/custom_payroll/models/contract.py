# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CustomPayrollContract(models.Model):
    _name = 'custom_payroll.contract'
    _description = 'Employee Contract'
    _order = 'date_start desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    # Basic Information
    name = fields.Char(string='Contract Reference', required=True, copy=False, default='New')
    employee_id = fields.Many2one('custom_payroll.employee', string='Employee', required=True, tracking=True)
    
    # Dates
    date_start = fields.Date(string='Start Date', required=True, tracking=True)
    date_end = fields.Date(string='End Date', tracking=True)
    trial_date_end = fields.Date(string='End of Trial Period')
    
    # Salary Information
    wage_type = fields.Selection([
        ('monthly', 'Monthly Fixed Wage'),
        ('hourly', 'Hourly Wage'),
        ('daily', 'Daily Wage'),
    ], string='Wage Type', default='monthly', required=True)
    
    wage = fields.Float(string='Wage', required=True, tracking=True)
    hourly_wage = fields.Float(string='Hourly Wage', compute='_compute_hourly_wage', store=True)
    
    # Working Schedule
    working_hours = fields.Float(string='Working Hours per Day', default=8.0)
    working_days = fields.Float(string='Working Days per Month', default=22.0)
    
    # Structure & Rules
    salary_structure_id = fields.Many2one('custom_payroll.salary_structure', string='Salary Structure', required=True, tracking=True)
    
    # Allowances (can override structure)
    housing_allowance = fields.Float(string='Housing Allowance', default=0)
    transport_allowance = fields.Float(string='Transport Allowance', default=0)
    medical_allowance = fields.Float(string='Medical Allowance', default=0)
    other_allowance = fields.Float(string='Other Allowance', default=0)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id', store=True)
    job_id = fields.Many2one('hr.job', string='Job Position', related='employee_id.job_id', store=True)
    notes = fields.Text(string='Notes')
    
    _sql_constraints = [
        ('date_check', 'CHECK(date_start <= date_end)', 'Contract start date must be before end date!'),
    ]
    
    @api.depends('wage', 'working_hours', 'working_days')
    def _compute_hourly_wage(self):
        for contract in self:
            if contract.wage_type == 'monthly' and contract.working_hours > 0 and contract.working_days > 0:
                contract.hourly_wage = contract.wage / (contract.working_hours * contract.working_days)
            elif contract.wage_type == 'hourly':
                contract.hourly_wage = contract.wage
            else:
                contract.hourly_wage = 0
    
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for contract in self:
            if contract.date_end and contract.date_start > contract.date_end:
                raise ValidationError('Contract start date must be before end date!')
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('custom_payroll.contract') or 'New'
        contract = super().create(vals)
        if contract.state == 'active':
            contract._deactivate_other_contracts()
        return contract
    
    def write(self, vals):
        if 'state' in vals and vals['state'] == 'active':
            self._deactivate_other_contracts()
        return super().write(vals)
    
    def _deactivate_other_contracts(self):
        for contract in self:
            other_contracts = self.search([
                ('employee_id', '=', contract.employee_id.id),
                ('id', '!=', contract.id),
                ('state', '=', 'active'),
            ])
            other_contracts.write({'state': 'expired'})
    
    def action_activate(self):
        self.write({'state': 'active'})
    
    def action_expire(self):
        self.write({'state': 'expired'})
    
    def action_cancel(self):
        self.write({'state': 'cancel'})
    
    def action_renew(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Renew Contract',
            'res_model': 'custom_payroll.contract',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_employee_id': self.employee_id.id},
        }
