{
    'name': 'Custom Payroll',
    'version': '1.0',
    'summary': 'Payroll Management with Accounting Integration',
    'description': """
        Complete payroll management system with accounting integration.
        Features:
        - Employee salary management
        - Payroll processing
        - Automatic accounting entries
        - Loan management
        - Tax and deduction handling
    """,
    'category': 'Human Resources',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'hr', 'custom_accounting'],
    'data': [
        'security/ir.model.access.csv',
        'data/accounting_data.xml',
        'views/payroll_account_mixin_views.xml',
        'views/salary_slip_views.xml',
        'views/salary_payment_views.xml',
        'views/employee_loan_views.xml',
        'wizard/payroll_setup_wizard_views.xml',
        'views/payroll_menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': '_post_init_payroll',
}
