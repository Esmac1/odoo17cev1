# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class CustomPayrollWorkEntry(models.Model):
    _name = 'custom_payroll.work_entry'
    _description = 'Work Entry'
    _order = 'date_start desc'
    
    name = fields.Char(string='Description', compute='_compute_name', store=True)
    employee_id = fields.Many2one('custom_payroll.employee', string='Employee', required=True)
    contract_id = fields.Many2one('custom_payroll.contract', string='Contract', required=True)
    date_start = fields.Datetime(string='Start Time', required=True)
    date_stop = fields.Datetime(string='Stop Time', required=True)
    date = fields.Date(string='Date', compute='_compute_date', store=True)
    work_entry_type_id = fields.Many2one('custom_payroll.work.entry.type', string='Work Entry Type', required=True)
    code = fields.Char(string='Code', related='work_entry_type_id.code', store=True)
    duration = fields.Float(string='Duration (hours)', compute='_compute_duration', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('validated', 'Validated'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft')
    payslip_id = fields.Many2one('custom_payroll.payslip', string='Payslip')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    notes = fields.Text(string='Notes')
    
    _sql_constraints = [
        ('date_check', 'CHECK(date_start < date_stop)', 'Start time must be before stop time!'),
    ]
    
    @api.depends('employee_id', 'work_entry_type_id', 'date_start')
    def _compute_name(self):
        for entry in self:
            employee_name = entry.employee_id.name or ''
            entry_type = entry.work_entry_type_id.name or ''
            date_str = entry.date_start.strftime('%Y-%m-%d') if entry.date_start else ''
            entry.name = f'{employee_name} - {entry_type} - {date_str}'
    
    @api.depends('date_start')
    def _compute_date(self):
        for entry in self:
            if entry.date_start:
                entry.date = entry.date_start.date()
            else:
                entry.date = False
    
    @api.depends('date_start', 'date_stop')
    def _compute_duration(self):
        for entry in self:
            if entry.date_start and entry.date_stop:
                delta = entry.date_stop - entry.date_start
                entry.duration = delta.total_seconds() / 3600
            else:
                entry.duration = 0
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    def action_validate(self):
        self.write({'state': 'validated'})
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})
