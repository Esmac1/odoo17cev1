{
    'name': 'Custom Accounting Extended Pro',
    'version': '1.0',
    'summary': 'Complete accounting system with advanced features',
    'description': """
        Advanced accounting system with:
        - Chart of Accounts
        - Journals and Transactions
        - Invoicing (Customer/Vendor)
        - Payments
        - Budget Management
        - Tax Management
        - Recurring Entries
    """,
    'author': 'Your Name',
    'website': 'https://yourwebsite.com',
    'category': 'Accounting',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_views.xml',
        'views/journal_views.xml',
        'views/move_views.xml',
        'views/tax_views.xml',
        'views/budget_views.xml',
        'views/payment_views.xml',
        'views/dashboard_views.xml',
        'views/invoice_views.xml',
        'views/recurring_views.xml',  # Add this if you created the file
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
