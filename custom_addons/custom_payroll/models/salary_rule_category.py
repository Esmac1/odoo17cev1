# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CustomPayrollSalaryRuleCategory(models.Model):
    _name = 'custom_payroll.salary_rule_category'
    _description = 'Salary Rule Category'
    
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    parent_id = fields.Many2one('custom_payroll.salary_rule_category', string='Parent')
    child_ids = fields.One2many('custom_payroll.salary_rule_category', 'parent_id', string='Children')
    total_debit = fields.Float(string='Total Debit', compute='_compute_totals')
    total_credit = fields.Float(string='Total Credit', compute='_compute_totals')
    balance = fields.Float(string='Balance', compute='_compute_totals')
    rule_ids = fields.One2many('custom_payroll.salary_rule', 'category_id', string='Rules')
    
    def _compute_totals(self):
        for category in self:
            category.total_debit = 0
            category.total_credit = 0
            category.balance = 0
