# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CustomPayrollSalaryStructure(models.Model):
    _name = 'custom_payroll.salary_structure'
    _description = 'Salary Structure'
    _order = 'name'
    
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    
    # Rules
    rule_ids = fields.Many2many('custom_payroll.salary_rule', string='Salary Rules',
                               relation='salary_structure_rule_rel',
                               column1='structure_id', column2='rule_id')
    
    # Default values
    default_basic = fields.Float(string='Default Basic Salary', default=0)
    default_housing = fields.Float(string='Default Housing Allowance', default=0)
    default_transport = fields.Float(string='Default Transport Allowance', default=0)
    default_medical = fields.Float(string='Default Medical Allowance', default=0)
    
    # Applies to
    applies_to = fields.Selection([
        ('all', 'All Employees'),
        ('department', 'Specific Department'),
        ('job', 'Specific Job Position'),
        ('grade', 'Salary Grade'),
    ], string='Applies To', default='all')
    
    department_id = fields.Many2one('hr.department', string='Department')
    job_id = fields.Many2one('hr.job', string='Job Position')
    grade_id = fields.Many2one('hr.salary.grade', string='Salary Grade')
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Relations
    contract_ids = fields.One2many('custom_payroll.contract', 'salary_structure_id', string='Contracts')
    
    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Code must be unique per company!'),
    ]
    
    def compute_salary(self, employee, contract, period_start, period_end):
        """Compute salary for an employee using this structure"""
        lines = []
        
        # Get basic salary from contract
        basic_salary = contract.wage
        
        # Compute each rule
        for rule in self.rule_ids:
            amount = rule.compute_rule(employee, contract, basic_salary, 0)
            if amount != 0:
                lines.append({
                    'name': rule.name,
                    'code': rule.code,
                    'category': 'allowance' if rule.rule_type == 'allowance' else 'deduction',
                    'amount': amount,
                    'quantity': 1,
                    'rate': 100,
                    'salary_rule_id': rule.id,
                    'account_debit': rule.account_debit.id if rule.account_debit else False,
                    'account_credit': rule.account_credit.id if rule.account_credit else False,
                })
        
        return lines
