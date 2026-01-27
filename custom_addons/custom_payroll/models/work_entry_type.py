# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CustomPayrollWorkEntryType(models.Model):
    _name = 'custom_payroll.work.entry.type'
    _description = 'Work Entry Type'
    _order = 'sequence, name'
    
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    category = fields.Selection([
        ('work', 'Work'),
        ('leave', 'Leave'),
        ('overtime', 'Overtime'),
        ('holiday', 'Holiday'),
        ('absence', 'Absence'),
        ('other', 'Other'),
    ], string='Category', default='work')
    is_paid = fields.Boolean(string='Paid', default=True)
    round_days = fields.Selection([
        ('no', 'No Rounding'),
        ('half', 'Half Day'),
        ('day', 'Full Day'),
    ], string='Round Days', default='no')
    rate = fields.Float(string='Rate (%)', default=100, help='Percentage of normal rate')
    color = fields.Integer(string='Color Index')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    notes = fields.Text(string='Notes')
    
    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Code must be unique per company!'),
    ]
