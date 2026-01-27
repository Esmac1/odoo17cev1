# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EmployeeLoan(models.Model):
    _name = 'custom_payroll.employee_loan'
    _description = 'Employee Loan'
    _inherit = ['mail.thread', 'payroll.account.mixin']
    
    name = fields.Char(string='Loan Reference', required=True, readonly=True, default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    
    loan_amount = fields.Float(string='Loan Amount', required=True)
    interest_rate = fields.Float(string='Interest Rate (%)', default=0.0)
    total_amount = fields.Float(string='Total Amount', compute='_compute_total', store=True)
    
    date_issued = fields.Date(string='Date Issued', required=True, default=fields.Date.today)
    repayment_start_date = fields.Date(string='Repayment Start Date', required=True)
    repayment_months = fields.Integer(string='Repayment Months', required=True, default=12)
    monthly_repayment = fields.Float(string='Monthly Repayment', compute='_compute_monthly_repayment', store=True)
    
    # Accounting
    journal_id = fields.Many2one('custom_accounting.journal', string='Journal')
    move_id = fields.Many2one('custom_accounting.move', string='Disbursement Journal Entry', readonly=True)
    
    company_id = fields.Many2one('res.company', string='Company', required=True, 
                                 default=lambda self: self.env.company)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('disbursed', 'Disbursed'),
        ('repaying', 'Repaying'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    note = fields.Text(string='Notes')
    
    @api.depends('loan_amount', 'interest_rate')
    def _compute_total(self):
        for loan in self:
            interest = (loan.loan_amount * loan.interest_rate) / 100
            loan.total_amount = loan.loan_amount + interest
    
    @api.depends('total_amount', 'repayment_months')
    def _compute_monthly_repayment(self):
        for loan in self:
            if loan.repayment_months > 0:
                loan.monthly_repayment = loan.total_amount / loan.repayment_months
            else:
                loan.monthly_repayment = 0.0
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('custom_payroll.employee_loan') or 'New'
        return super().create(vals)
    
    def action_approve(self):
        """Approve loan"""
        for loan in self:
            loan.write({'state': 'approved'})
            loan.message_post(body=_("Loan approved"))
        return True
    
    def action_disburse(self):
        """Disburse loan and create accounting entry"""
        for loan in self:
            if loan.state != 'approved':
                raise UserError(_("Only approved loans can be disbursed"))
            
            # Create accounting entry for loan disbursement
            move = loan._create_disbursement_entry()
            
            loan.write({
                'state': 'disbursed',
                'move_id': move.id,
            })
            
            loan.message_post(body=_("Loan disbursed. Journal Entry: %s") % move.name)
        
        return True
    
    def _create_disbursement_entry(self):
        """Create journal entry for loan disbursement"""
        self.ensure_one()
        
        # Get accounts
        loan_receivable_acc = self._get_payroll_account('loan_receivable', self.company_id.id)
        bank_account = self._get_bank_account(self.company_id.id)
        
        # Get or create loan journal
        journal = self.journal_id or self.env['custom_accounting.journal'].search([
            ('code', '=', 'LOAN'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not journal:
            journal = self.env['custom_accounting.journal'].create({
                'name': 'Loan Journal',
                'code': 'LOAN',
                'type': 'general',
                'company_id': self.company_id.id,
            })
        
        # Journal entry lines
        lines = [
            # Debit: Loan Receivable (asset - employee owes company)
            (0, 0, {
                'account_id': loan_receivable_acc.id,
                'debit': self.loan_amount,
                'credit': 0,
                'name': f'Loan to {self.employee_id.name}',
                'partner_id': self.employee_id.user_id.partner_id.id if self.employee_id.user_id else False,
            }),
            # Credit: Bank Account (money leaves company)
            (0, 0, {
                'account_id': bank_account.id,
                'debit': 0,
                'credit': self.loan_amount,
                'name': f'Loan Disbursement - {self.employee_id.name}',
            }),
        ]
        
        # Create journal entry
        move = self.env['custom_accounting.move'].create({
            'name': f'LOAN/{self.date_issued}/{self.name}',
            'date': self.date_issued,
            'ref': f'Loan Disbursement: {self.name} - {self.employee_id.name}',
            'journal_id': journal.id,
            'line_ids': lines,
            'state': 'posted',
        })
        
        return move
    
    def action_start_repayment(self):
        """Start loan repayment"""
        for loan in self:
            loan.write({'state': 'repaying'})
            loan.message_post(body=_("Loan repayment started"))
        return True
    
    def action_mark_paid(self):
        """Mark loan as fully paid"""
        for loan in self:
            loan.write({'state': 'paid'})
            loan.message_post(body=_("Loan fully paid"))
        return True
    
    def action_cancel(self):
        """Cancel loan"""
        for loan in self:
            if loan.state == 'disbursed':
                raise UserError(_("Cannot cancel a disbursed loan"))
            
            loan.write({'state': 'cancelled'})
            loan.message_post(body=_("Loan cancelled"))
        
        return True
    
    def action_view_journal_entry(self):
        """View the disbursement journal entry"""
        self.ensure_one()
        if not self.move_id:
            raise UserError(_("No journal entry created yet"))
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Loan Journal Entry',
            'res_model': 'custom_accounting.move',
            'res_id': self.move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
