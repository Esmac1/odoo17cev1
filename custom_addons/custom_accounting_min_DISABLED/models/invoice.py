# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

class CustomInvoice(models.Model):
    _name = 'custom_accounting.invoice'
    _description = 'Invoice'
    
    name = fields.Char(string='Number', default='/', readonly=True)
    invoice_date = fields.Date(default=fields.Date.today, required=True)
    due_date = fields.Date(default=lambda self: fields.Date.today() + timedelta(days=30), required=True)
    
    type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
    ], default='out_invoice', required=True)
    
    partner_id = fields.Many2one('res.partner', string='Customer/Vendor', required=True)
    journal_id = fields.Many2one('custom_accounting.journal', required=True)
    
    invoice_line_ids = fields.One2many('custom_accounting.invoice.line', 'invoice_id', string='Lines')
    
    amount_total = fields.Float(compute='_compute_amounts', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ], default='draft')
    
    move_id = fields.Many2one('custom_accounting.move', readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    
    @api.depends('invoice_line_ids.subtotal')
    def _compute_amounts(self):
        for invoice in self:
            invoice.amount_total = sum(invoice.invoice_line_ids.mapped('subtotal'))
    
    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            if vals.get('type', 'out_invoice') == 'out_invoice':
                vals['name'] = self.env['ir.sequence'].next_by_code('custom_accounting.invoice.customer') or '/'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('custom_accounting.invoice.vendor') or '/'
        return super().create(vals)
    
    def action_post(self):
        for invoice in self:
            if invoice.state != 'draft':
                raise UserError(_("Only draft invoices can be posted!"))
            
            # Find an account
            account = self.env['custom_accounting.account'].search([], limit=1)
            if not account:
                account = self.env['custom_accounting.account'].create({
                    'name': 'Default Account',
                    'code': '100000',
                    'type': 'asset',
                })
            
            # Create journal entry
            move_lines = [(0, 0, {
                'name': invoice.name,
                'account_id': account.id,
                'partner_id': invoice.partner_id.id,
                'debit': invoice.amount_total if invoice.type == 'out_invoice' else 0,
                'credit': invoice.amount_total if invoice.type == 'in_invoice' else 0,
            })]
            
            for line in invoice.invoice_line_ids:
                move_lines.append((0, 0, {
                    'name': line.name,
                    'account_id': line.account_id.id,
                    'debit': line.subtotal if invoice.type == 'in_invoice' else 0,
                    'credit': line.subtotal if invoice.type == 'out_invoice' else 0,
                }))
            
            move = self.env['custom_accounting.move'].create({
                'date': invoice.invoice_date,
                'journal_id': invoice.journal_id.id,
                'ref': invoice.name,
                'line_ids': move_lines,
            })
            move.action_post()
            invoice.move_id = move
            invoice.state = 'posted'
            return True
    
    def action_cancel(self):
        for invoice in self:
            if invoice.move_id:
                invoice.move_id.action_cancel()
            invoice.state = 'cancelled'
            return True

class InvoiceLine(models.Model):
    _name = 'custom_accounting.invoice.line'
    _description = 'Invoice Line'
    
    invoice_id = fields.Many2one('custom_accounting.invoice', required=True, ondelete='cascade')
    name = fields.Char(required=True)
    account_id = fields.Many2one('custom_accounting.account', required=True)
    quantity = fields.Float(default=1.0)
    price_unit = fields.Float(required=True)
    subtotal = fields.Float(compute='_compute_subtotal', store=True)
    
    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit

class PaymentTerm(models.Model):
    _name = 'custom_accounting.payment.term'
    _description = 'Payment Terms'
    
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

class PaymentTermLine(models.Model):
    _name = 'custom_accounting.payment.term.line'
    _description = 'Payment Term Line'
    
    payment_term_id = fields.Many2one('custom_accounting.payment.term', required=True)
    value = fields.Float(required=True)
    days = fields.Integer(default=0)
