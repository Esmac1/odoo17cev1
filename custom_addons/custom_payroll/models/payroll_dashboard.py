# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta

class CustomPayrollDashboard(models.Model):
    _name = 'custom_payroll.payroll_dashboard'
    _description = 'Payroll Dashboard'
    _auto = False  # This is a SQL view
    
    # These fields will be populated by SQL query
    month = fields.Char(string='Month')
    total_employees = fields.Integer(string='Total Employees')
    total_payslips = fields.Integer(string='Total Payslips')
    total_basic = fields.Float(string='Total Basic Salary')
    total_gross = fields.Float(string='Total Gross Salary')
    total_deductions = fields.Float(string='Total Deductions')
    total_net = fields.Float(string='Total Net Salary')
    avg_salary = fields.Float(string='Average Salary')
    
    def init(self):
        """Initialize the SQL view"""
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW custom_payroll_payroll_dashboard AS (
                SELECT 
                    ROW_NUMBER() OVER () as id,
                    TO_CHAR(date_from, 'YYYY-MM') as month,
                    COUNT(DISTINCT employee_id) as total_employees,
                    COUNT(*) as total_payslips,
                    SUM(basic_salary) as total_basic,
                    SUM(gross_salary) as total_gross,
                    SUM(total_deductions) as total_deductions,
                    SUM(net_salary) as total_net,
                    AVG(net_salary) as avg_salary
                FROM custom_payroll_payslip
                WHERE state IN ('confirmed', 'paid')
                GROUP BY TO_CHAR(date_from, 'YYYY-MM')
                ORDER BY month DESC
            )
        """)
