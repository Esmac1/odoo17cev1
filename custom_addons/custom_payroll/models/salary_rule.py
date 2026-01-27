# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CustomPayrollSalaryRule(models.Model):
    _name = 'custom_payroll.salary_rule'
    _description = 'Salary Rule'
    _order = 'sequence, code'
    
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    category_id = fields.Many2one('custom_payroll.salary_rule_category', string='Category', required=True)
    
    # Type
    rule_type = fields.Selection([
        ('allowance', 'Allowance'),
        ('deduction', 'Deduction'),
        ('total', 'Total'),
    ], string='Type', required=True, default='allowance')
    
    # Computation
    amount_type = fields.Selection([
        ('fixed', 'Fixed Amount'),
        ('percentage', 'Percentage of Basic'),
        ('percentage_gross', 'Percentage of Gross'),
        ('formula', 'Formula'),
    ], string='Amount Type', default='fixed')
    
    amount = fields.Float(string='Amount/Percentage', default=0)
    amount_formula = fields.Char(string='Formula')
    
    # Conditions
    condition_select = fields.Selection([
        ('none', 'Always True'),
        ('range', 'Range'),
        ('python', 'Python Expression'),
    ], string='Condition Based On', default='none')
    
    condition_range = fields.Char(string='Range')
    condition_python = fields.Text(string='Python Condition')
    
    # Applies to
    applies_to = fields.Selection([
        ('all', 'All Employees'),
        ('department', 'Specific Department'),
        ('job', 'Specific Job Position'),
        ('tag', 'Employee Tags'),
    ], string='Applies To', default='all')
    
    department_id = fields.Many2one('hr.department', string='Department')
    job_id = fields.Many2one('hr.job', string='Job Position')
    tag_ids = fields.Many2many('hr.employee.category', string='Employee Tags')
    
    # Accounting
    account_debit = fields.Many2one('custom_accounting.account', string='Debit Account')
    account_credit = fields.Many2one('custom_accounting.account', string='Credit Account')
    journal_id = fields.Many2one('custom_accounting.journal', string='Journal')
    
    # Structure relation
    structure_ids = fields.Many2many('custom_payroll.salary_structure', string='Structures')
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Code must be unique per company!'),
    ]
    
    def compute_rule(self, employee, contract, basic_salary, gross_salary):
        """Compute the amount for this rule"""
        amount = 0
        
        # Check conditions
        if not self._check_conditions(employee):
            return 0
        
        # Compute based on amount type
        if self.amount_type == 'fixed':
            amount = self.amount
        elif self.amount_type == 'percentage':
            amount = basic_salary * (self.amount / 100)
        elif self.amount_type == 'percentage_gross':
            amount = gross_salary * (self.amount / 100)
        elif self.amount_type == 'formula' and self.amount_formula:
            # Simple formula evaluation (in real implementation, use safe_eval)
            try:
                amount = eval(self.amount_formula, {
                    'basic': basic_salary,
                    'gross': gross_salary,
                    'contract': contract,
                    'employee': employee,
                })
            except:
                amount = 0
        
        return amount
    
    def _check_conditions(self, employee):
        """Check if rule applies to this employee"""
        if self.condition_select == 'none':
            return True
        elif self.condition_select == 'range':
            # Implement range checking
            return True
        elif self.condition_select == 'python':
            # Implement Python condition checking
            return True
        
        # Check applies_to conditions
        if self.applies_to == 'all':
            return True
        elif self.applies_to == 'department' and employee.department_id == self.department_id:
            return True
        elif self.applies_to == 'job' and employee.job_id == self.job_id:
            return True
        elif self.applies_to == 'tag' and any(tag in employee.category_ids for tag in self.tag_ids):
            return True
        
        return False
