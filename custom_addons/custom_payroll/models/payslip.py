# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class CustomPayrollPayslip(models.Model):
    _name = 'custom_payroll.payslip'
    _description = 'Payslip'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc, employee_id'
    
    # Basic Information
    name = fields.Char(string='Payslip Number', required=True, copy=False, default='New')
    employee_id = fields.Many2one('custom_payroll.employee', string='Employee', required=True, tracking=True)
    contract_id = fields.Many2one('custom_payroll.contract', string='Contract', required=True)
    
    # Period
    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)
    date_payment = fields.Date(string='Payment Date')
    
    # Salary Structure
    salary_structure_id = fields.Many2one('custom_payroll.salary_structure', string='Salary Structure',
                                         related='contract_id.salary_structure_id', store=True)
    
    # Components
    line_ids = fields.One2many('custom_payroll.payslip_line', 'slip_id', string='Payslip Lines')
    worked_days_ids = fields.One2many('custom_payroll.worked_days', 'payslip_id', string='Worked Days')
    leave_days_ids = fields.One2many('custom_payroll.leave_days', 'payslip_id', string='Leave Days')
    
    # Totals
    basic_salary = fields.Float(string='Basic Salary', compute='_compute_totals', store=True)
    total_allowances = fields.Float(string='Total Allowances', compute='_compute_totals', store=True)
    total_deductions = fields.Float(string='Total Deductions', compute='_compute_totals', store=True)
    gross_salary = fields.Float(string='Gross Salary', compute='_compute_totals', store=True)
    net_salary = fields.Float(string='Net Salary', compute='_compute_totals', store=True)
    
    # Nigerian Deductions
    paye_tax = fields.Float(string='PAYE Tax', compute='_compute_tax', store=True)
    nssf_deduction = fields.Float(string='NSSF', compute='_compute_statutory', store=True)
    nhif_deduction = fields.Float(string='NHIF', compute='_compute_statutory', store=True)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verified', 'Verified'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    # Batch Processing
    payslip_run_id = fields.Many2one('custom_payroll.payslip_run', string='Payslip Batch')
    
    # Accounting
    journal_entry_id = fields.Many2one('custom_accounting.move', string='Journal Entry')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Notes
    notes = fields.Text(string='Notes')
    
    _sql_constraints = [
        ('date_check', 'CHECK(date_from <= date_to)', 'Start date must be before end date!'),
    ]
    
    @api.depends('line_ids', 'line_ids.total', 'line_ids.category')
    def _compute_totals(self):
        for payslip in self:
            payslip.basic_salary = sum(payslip.line_ids.filtered(
                lambda l: l.code == 'BASIC').mapped('total'))
            payslip.total_allowances = sum(payslip.line_ids.filtered(
                lambda l: l.category == 'allowance').mapped('total'))
            payslip.total_deductions = sum(payslip.line_ids.filtered(
                lambda l: l.category == 'deduction').mapped('total'))
            payslip.gross_salary = payslip.basic_salary + payslip.total_allowances
            payslip.net_salary = payslip.gross_salary - payslip.total_deductions
    
    @api.depends('gross_salary')
    def _compute_tax(self):
        # Simplified PAYE calculation - should be replaced with actual Nigerian tax brackets
        for payslip in self:
            gross = payslip.gross_salary
            if gross <= 30000:
                payslip.paye_tax = gross * 0.07
            elif gross <= 60000:
                payslip.paye_tax = 2100 + ((gross - 30000) * 0.11)
            elif gross <= 110000:
                payslip.paye_tax = 5400 + ((gross - 60000) * 0.15)
            elif gross <= 160000:
                payslip.paye_tax = 12900 + ((gross - 110000) * 0.19)
            elif gross <= 320000:
                payslip.paye_tax = 22400 + ((gross - 160000) * 0.21)
            else:
                payslip.paye_tax = 56000 + ((gross - 320000) * 0.24)
    
    @api.depends('basic_salary')
    def _compute_statutory(self):
        for payslip in self:
            # NSSF: 5% of basic salary (employee contribution)
            payslip.nssf_deduction = payslip.basic_salary * 0.05 if payslip.basic_salary > 0 else 0
            
            # NHIF: Tiered based on basic salary
            basic = payslip.basic_salary
            if basic <= 5999:
                payslip.nhif_deduction = 150
            elif basic <= 7999:
                payslip.nhif_deduction = 300
            elif basic <= 11999:
                payslip.nhif_deduction = 400
            elif basic <= 14999:
                payslip.nhif_deduction = 500
            elif basic <= 19999:
                payslip.nhif_deduction = 600
            elif basic <= 24999:
                payslip.nhif_deduction = 750
            elif basic <= 29999:
                payslip.nhif_deduction = 850
            elif basic <= 34999:
                payslip.nhif_deduction = 900
            elif basic <= 39999:
                payslip.nhif_deduction = 950
            elif basic <= 44999:
                payslip.nhif_deduction = 1000
            elif basic <= 49999:
                payslip.nhif_deduction = 1100
            elif basic <= 59999:
                payslip.nhif_deduction = 1200
            elif basic <= 69999:
                payslip.nhif_deduction = 1300
            elif basic <= 79999:
                payslip.nhif_deduction = 1400
            elif basic <= 89999:
                payslip.nhif_deduction = 1500
            elif basic <= 99999:
                payslip.nhif_deduction = 1600
            else:
                payslip.nhif_deduction = 1700
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('custom_payroll.payslip') or 'New'
        return super().create(vals)
    
    def action_verify(self):
        self.write({'state': 'verified'})
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    def action_pay(self):
        self._create_accounting_entry()
        self.write({'state': 'paid', 'date_payment': fields.Date.today()})
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})
    
    def action_compute_sheet(self):
        """Compute the payslip lines based on salary rules"""
        for payslip in self:
            # Clear existing lines
            payslip.line_ids.unlink()
            
            # Get salary rules from structure
            rules = payslip.salary_structure_id.rule_ids
            lines = []
            
            # Add basic salary
            lines.append((0, 0, {
                'name': 'Basic Salary',
                'code': 'BASIC',
                'category': 'allowance',
                'amount': payslip.contract_id.wage,
                'quantity': 1,
                'rate': 100,
            }))
            
            # Add allowances from contract
            lines.append((0, 0, {
                'name': 'Housing Allowance',
                'code': 'HOUSE',
                'category': 'allowance',
                'amount': payslip.contract_id.housing_allowance,
                'quantity': 1,
                'rate': 100,
            }))
            
            lines.append((0, 0, {
                'name': 'Transport Allowance',
                'code': 'TRANS',
                'category': 'allowance',
                'amount': payslip.contract_id.transport_allowance,
                'quantity': 1,
                'rate': 100,
            }))
            
            # Add statutory deductions
            lines.append((0, 0, {
                'name': 'PAYE Tax',
                'code': 'PAYE',
                'category': 'deduction',
                'amount': payslip.paye_tax,
                'quantity': 1,
                'rate': 100,
            }))
            
            lines.append((0, 0, {
                'name': 'NSSF Contribution',
                'code': 'NSSF',
                'category': 'deduction',
                'amount': payslip.nssf_deduction,
                'quantity': 1,
                'rate': 100,
            }))
            
            lines.append((0, 0, {
                'name': 'NHIF Contribution',
                'code': 'NHIF',
                'category': 'deduction',
                'amount': payslip.nhif_deduction,
                'quantity': 1,
                'rate': 100,
            }))
            
            # Add totals
            lines.append((0, 0, {
                'name': 'Gross Salary',
                'code': 'GROSS',
                'category': 'total',
                'amount': payslip.gross_salary,
                'quantity': 1,
                'rate': 100,
            }))
            
            lines.append((0, 0, {
                'name': 'Total Deductions',
                'code': 'DEDUCT',
                'category': 'total',
                'amount': payslip.total_deductions,
                'quantity': 1,
                'rate': 100,
            }))
            
            lines.append((0, 0, {
                'name': 'Net Salary',
                'code': 'NET',
                'category': 'total',
                'amount': payslip.net_salary,
                'quantity': 1,
                'rate': 100,
            }))
            
            payslip.line_ids = lines
    
    def _create_accounting_entry(self):
        """Create accounting journal entry for the payslip"""
        # This should integrate with your custom_accounting module
        # For now, it's a placeholder
        pass
    
    def action_print_payslip(self):
        return self.env.ref('custom_payroll.report_payslip').report_action(self)
