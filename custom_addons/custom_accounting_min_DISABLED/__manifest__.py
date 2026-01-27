{
    'name': 'Custom Accounting Extended Pro',
    'version': '1.0.0',
    'summary': 'Complete accounting system with advanced features',
    'description': """
        Advanced accounting system with:
        - Multi-currency support
        - Enhanced financial dashboard
        - Advanced financial reporting
        - Chart of Accounts with hierarchy
        - Journals and Transactions
        - Invoicing (Customer/Vendor)
        - Payments
        - Budget Management
        - Tax Management
        - Recurring Entries
        - Assets Management
        - Bank Reconciliation
        - Trial Balance Reports
    """,
    'author': 'Your Name',
    'website': 'https://yourwebsite.com',
    'category': 'Accounting',
    'depends': ['base', 'mail', 'web', 'hr', 'account'],
    'data': [
        'data/sequences.xml',
        'security/ir.model.access.csv',
        'views/account_views.xml',
        'views/journal_views.xml',
        'views/move_views.xml',
        'views/tax_views.xml',
        'views/budget_views.xml',
        'views/payment_views.xml',
        'views/dashboard_views.xml',
        'views/enhanced_dashboard_views.xml',
        'views/invoice_views.xml',
        'views/asset_views.xml',
        'views/asset_category_views.xml',
        'views/asset_depreciation_views.xml',
        'views/recurring_transaction_views.xml',
        'views/reconciliation_views.xml',
        'views/trial_balance_views.xml',
        'views/financial_report_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'custom_accounting_min/static/src/css/dashboard.css',
        ],
    },
    'license': 'LGPL-3',
}
