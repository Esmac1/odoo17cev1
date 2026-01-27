# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date

class CustomBudget(models.Model):
    _name = 'custom_accounting.budget'
    _description = 'Budget'
    _order = 'fiscal_year desc, name'
    
    name = fields.Char(string='Budget Name', required=True)
    code = fields.Char(string='Budget Code', required=True)
    fiscal_year = fields.Char(string='Fiscal Year', required=True, default=lambda self: str(date.today().year))
    date_from = fields.Date(string='From Date', required=True, default=lambda self: date(date.today().year, 1, 1))
    date_to = fields.Date(string='To Date', required=True, default=lambda self: date(date.today().year, 12, 31))
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('closed', 'Closed')
    ], string='Status', default='draft', required=True)
    
    line_ids = fields.One2many('custom_accounting.budget.line', 'budget_id', string='Budget Lines')
    
    total_budget = fields.Float(string='Total Budget', compute='_compute_totals', store=True, digits=(16, 2))
    total_actual = fields.Float(string='Total Actual', compute='_compute_totals', store=True, digits=(16, 2))
    total_variance = fields.Float(string='Total Variance', compute='_compute_totals', store=True, digits=(16, 2))
    variance_percentage = fields.Float(string='Variance %', compute='_compute_totals', store=True, digits=(12, 2))
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    
    @api.depends('line_ids.budget_amount', 'line_ids.actual_amount')
    def _compute_totals(self):
        for budget in self:
            total_budget = sum(line.budget_amount for line in budget.line_ids)
            total_actual = sum(line.actual_amount for line in budget.line_ids)
            total_variance = total_budget - total_actual
            
            budget.total_budget = total_budget
            budget.total_actual = total_actual
            budget.total_variance = total_variance
            budget.variance_percentage = (total_variance / total_budget * 100) if total_budget != 0 else 0.0
    
    def action_submit(self):
        for budget in self:
            if budget.state != 'draft':
                raise UserError(_('Only draft budgets can be submitted.'))
            budget.write({'state': 'submitted'})
    
    def action_approve(self):
        for budget in self:
            if budget.state != 'submitted':
                raise UserError(_('Only submitted budgets can be approved.'))
            budget.write({'state': 'approved'})
    
    def action_reject(self):
        for budget in self:
            if budget.state != 'submitted':
                raise UserError(_('Only submitted budgets can be rejected.'))
            budget.write({'state': 'rejected'})
    
    def action_close(self):
        for budget in self:
            if budget.state not in ['approved', 'submitted']:
                raise UserError(_('Only approved or submitted budgets can be closed.'))
            budget.write({'state': 'closed'})
    
    def action_reopen(self):
        for budget in self:
            if budget.state != 'closed':
                raise UserError(_('Only closed budgets can be reopened.'))
            budget.write({'state': 'draft'})

class CustomBudgetLine(models.Model):
    _name = 'custom_accounting.budget.line'
    _description = 'Budget Line'
    _order = 'sequence, id'
    
    budget_id = fields.Many2one('custom_accounting.budget', string='Budget', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    
    account_id = fields.Many2one('custom_accounting.account', string='Account', required=True)
    account_code = fields.Char(string='Account Code', related='account_id.code', store=True, readonly=True)
    account_name = fields.Char(string='Account Name', related='account_id.name', store=True, readonly=True)
    
    budget_amount = fields.Float(string='Budget Amount', required=True, digits=(16, 2))
    actual_amount = fields.Float(string='Actual Amount', compute='_compute_actual', store=True, digits=(16, 2))
    variance_amount = fields.Float(string='Variance Amount', compute='_compute_variance', store=True, digits=(16, 2))
    variance_percentage = fields.Float(string='Variance %', compute='_compute_variance', store=True, digits=(12, 2))
    
    status = fields.Selection([
        ('on_budget', 'On Budget'),
        ('over_budget', 'Over Budget'),
        ('under_budget', 'Under Budget'),
    ], string='Status', compute='_compute_status', store=True)
    
    notes = fields.Text(string='Notes')
    
    @api.depends('account_id')
    def _compute_actual(self):
        for line in self:
            line.actual_amount = line.budget_amount * 0.8
    
    @api.depends('budget_amount', 'actual_amount')
    def _compute_variance(self):
        for line in self:
            line.variance_amount = line.budget_amount - line.actual_amount
            line.variance_percentage = (line.variance_amount / line.budget_amount * 100) if line.budget_amount != 0 else 0.0
    
    @api.depends('variance_amount')
    def _compute_status(self):
        for line in self:
            if abs(line.variance_amount) < 0.01:
                line.status = 'on_budget'
            elif line.variance_amount > 0:
                line.status = 'under_budget'
            else:
                line.status = 'over_budget'
    
    @api.constrains('budget_amount')
    def _check_budget_amount(self):
        for line in self:
            if line.budget_amount < 0:
                raise ValidationError(_('Budget amount cannot be negative.'))
