# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date

class CustomBudget(models.Model):
    _name = 'custom_accounting.budget'
    _description = 'Budget'
    _order = 'fiscal_year desc, name'
    
    # ========== BASIC FIELDS ==========
    name = fields.Char(string='Budget Name', required=True)
    code = fields.Char(string='Budget Code', required=True, 
                      default=lambda self: self.env['ir.sequence'].next_by_code('custom_accounting.budget'))
    
    # ========== PERIOD ==========
    fiscal_year = fields.Char(string='Fiscal Year', required=True, 
                             default=lambda self: str(date.today().year))
    date_from = fields.Date(string='From Date', required=True, 
                           default=lambda self: date(date.today().year, 1, 1))
    date_to = fields.Date(string='To Date', required=True,
                         default=lambda self: date(date.today().year, 12, 31))
    
    # ========== STATUS ==========
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('closed', 'Closed')
    ], string='Status', default='draft', required=True, tracking=True)
    
    # ========== BUDGET LINES ==========
    line_ids = fields.One2many('custom_accounting.budget.line', 'budget_id', string='Budget Lines')
    
    # ========== COMPUTED FIELDS ==========
    total_budget = fields.Float(string='Total Budget', compute='_compute_totals', store=True, digits=(16, 2))
    total_actual = fields.Float(string='Total Actual', compute='_compute_totals', store=True, digits=(16, 2))
    total_variance = fields.Float(string='Total Variance', compute='_compute_totals', store=True, digits=(16, 2))
    variance_percentage = fields.Float(string='Variance %', compute='_compute_totals', store=True, digits=(12, 2))
    
    # ========== COMPANY ==========
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True, index=True)
    
    # ========== COMPUTE METHODS ==========
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
    
    # ========== ACTION METHODS ==========
    def action_submit(self):
        for budget in self:
            if budget.state != 'draft':
                raise UserError(_('Only draft budgets can be submitted.'))
            
            if not budget.line_ids:
                raise UserError(_('Cannot submit a budget without any lines.'))
            
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
    
    # ========== HELPER METHODS ==========
    def get_budget_performance(self):
        """Get budget performance analysis"""
        performance = {
            'on_budget': 0,
            'over_budget': 0,
            'under_budget': 0,
            'total_lines': len(self.line_ids),
        }
        
        for line in self.line_ids:
            if line.variance_amount == 0:
                performance['on_budget'] += 1
            elif line.variance_amount > 0:  # Positive variance = under budget
                performance['under_budget'] += 1
            else:  # Negative variance = over budget
                performance['over_budget'] += 1
        
        return performance

class CustomBudgetLine(models.Model):
    _name = 'custom_accounting.budget.line'
    _description = 'Budget Line'
    _order = 'sequence, id'
    
    # ========== BASIC FIELDS ==========
    budget_id = fields.Many2one('custom_accounting.budget', string='Budget', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    
    # ========== ACCOUNT ==========
    account_id = fields.Many2one('custom_accounting.account', string='Account', required=True, 
                                domain="[('type', 'in', ['income', 'expense'])]")
    account_code = fields.Char(string='Account Code', related='account_id.code', store=True, readonly=True)
    account_name = fields.Char(string='Account Name', related='account_id.name', store=True, readonly=True)
    account_type = fields.Selection(string='Account Type', related='account_id.type', store=True, readonly=True)
    
    # ========== AMOUNTS ==========
    budget_amount = fields.Float(string='Budget Amount', required=True, digits=(16, 2))
    actual_amount = fields.Float(string='Actual Amount', compute='_compute_actual', store=True, digits=(16, 2))
    variance_amount = fields.Float(string='Variance Amount', compute='_compute_variance', store=True, digits=(16, 2))
    variance_percentage = fields.Float(string='Variance %', compute='_compute_variance', store=True, digits=(12, 2))
    
    # ========== STATUS ==========
    status = fields.Selection([
        ('on_budget', 'On Budget'),
        ('over_budget', 'Over Budget'),
        ('under_budget', 'Under Budget'),
    ], string='Status', compute='_compute_status', store=True)
    
    # ========== NOTES ==========
    notes = fields.Text(string='Notes')
    
    # ========== COMPUTE METHODS ==========
    @api.depends('account_id')
    def _compute_actual(self):
        # Simplified - in production, this would compute from actual transactions
        for line in self:
            line.actual_amount = line.budget_amount * 0.8  # Example: 80% of budget
    
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
    
    # ========== CONSTRAINTS ==========
    @api.constrains('budget_amount')
    def _check_budget_amount(self):
        for line in self:
            if line.budget_amount < 0:
                raise ValidationError(_('Budget amount cannot be negative.'))
    
    # ========== ONCHANGE METHODS ==========
    @api.onchange('account_id')
    def _onchange_account_id(self):
        if self.account_id:
            self.account_code = self.account_id.code
            self.account_name = self.account_id.name
