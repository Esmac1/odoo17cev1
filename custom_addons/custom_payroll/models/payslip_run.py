# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class CustomPayrollPayslipRun(models.Model):
    _name = 'custom_payroll.payslip_run'
    _description = 'Payslip Batch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc'
    
    name = fields.Char(string='Batch Name', required=True, default='New')
    date_start = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_end = fields.Date(string='End Date', required=True)
    date_payment = fields.Date(string='Payment Date')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verified', 'Verified'),
        ('done', 'Done'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    payslip_ids = fields.One2many('custom_payroll.payslip', 'payslip_run_id', string='Payslips')
    
    # Totals
    total_basic = fields.Float(string='Total Basic', compute='_compute_totals', store=True)
    total_gross = fields.Float(string='Total Gross', compute='_compute_totals', store=True)
    total_deductions = fields.Float(string='Total Deductions', compute='_compute_totals', store=True)
    total_net = fields.Float(string='Total Net', compute='_compute_totals', store=True)
    total_employees = fields.Integer(string='Number of Employees', compute='_compute_totals', store=True)
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    journal_entry_id = fields.Many2one('custom_accounting.move', string='Journal Entry')
    notes = fields.Text(string='Notes')
    
    @api.depends('payslip_ids', 'payslip_ids.basic_salary', 'payslip_ids.gross_salary',
                'payslip_ids.total_deductions', 'payslip_ids.net_salary')
    def _compute_totals(self):
        for batch in self:
            batch.total_basic = sum(batch.payslip_ids.mapped('basic_salary'))
            batch.total_gross = sum(batch.payslip_ids.mapped('gross_salary'))
            batch.total_deductions = sum(batch.payslip_ids.mapped('total_deductions'))
            batch.total_net = sum(batch.payslip_ids.mapped('net_salary'))
            batch.total_employees = len(batch.payslip_ids)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('custom_payroll.payslip_run') or 'New'
        return super().create(vals)
    
    def action_confirm(self):
        self.write({'state': 'verified'})
    
    def action_done(self):
        self.write({'state': 'done'})
    
    def action_pay(self):
        self._create_batch_accounting_entry()
        self.write({'state': 'paid', 'date_payment': fields.Date.today()})
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})
    
    def action_generate_payslips(self):
        """Generate payslips for all active employees"""
        active_employees = self.env['custom_payroll.employee'].search([
            ('payroll_active', '=', True),
            ('active_contract_id', '!=', False),
        ])
        
        payslips = []
        for employee in active_employees:
            payslip = self.env['custom_payroll.payslip'].create({
                'employee_id': employee.id,
                'contract_id': employee.active_contract_id.id,
                'date_from': self.date_start,
                'date_to': self.date_end,
                'date_payment': self.date_payment,
                'payslip_run_id': self.id,
            })
            payslip.action_compute_sheet()
            payslips.append(payslip.id)
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generated Payslips',
            'res_model': 'custom_payroll.payslip',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', payslips)],
        }
    
    def _create_batch_accounting_entry(self):
        """Create accounting journal entry for the entire batch"""
        # This should integrate with your custom_accounting module
        pass
    
    def action_print_summary(self):
        return self.env.ref('custom_payroll.report_payroll_summary').report_action(self)
