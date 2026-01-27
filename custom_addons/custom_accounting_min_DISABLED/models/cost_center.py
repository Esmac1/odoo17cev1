# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CostCenter(models.Model):
    _name = 'custom_accounting.cost.center'
    _description = 'Cost Center'
    
    name = fields.Char(string='Cost Center Name', required=True)
    code = fields.Char(string='Cost Center Code', required=True, size=10)
    parent_id = fields.Many2one('custom_accounting.cost.center', string='Parent Cost Center')
    child_ids = fields.One2many('custom_accounting.cost.center', 'parent_id', 
                               string='Child Cost Centers')
    
    manager_id = fields.Many2one('res.users', string='Cost Center Manager')
    department_id = fields.Many2one('hr.department', string='Department')
    
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company)
    
    description = fields.Text(string='Description')
    
    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 
         'Cost center code must be unique per company!'),
    ]
