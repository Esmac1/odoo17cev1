{
    'name': 'Custom Accounting Extended',
    'version': '3.0',
    'category': 'Accounting',
    'summary': 'Standalone accounting: accounts, journals, moves, assets, bank and reconciliation for Odoo CE',
    'author': 'You',
    'depends': ['base', 'mail', 'purchase'],
    'data': [
        # Security
        'security/ir.model.access.csv',

        # Data & sequences
        'data/sequence.xml',
        'data/chart_of_accounts.xml',
        'data/cron.xml',

        # Core accounting views first (actions must exist before menu)
        'views/account_views.xml',
        'views/journal_views.xml',
        'views/move_views.xml',
        'views/report_views.xml',  # Updated with Balance Sheet & P&L

        # NEW: Dashboard
        'views/dashboard_views.xml',

        # Menu (after actions)
        'views/menu.xml',  # Updated with Dashboard + Reports

        # Other features
        'views/asset_views.xml',
        'views/recurring_transaction_views.xml',
        'views/bank_transaction_views.xml',
        'views/reconciliation_views.xml',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
