{
    'name': 'Discuss Realtime Notify',
    'version': '1.0',
    'category': 'Discuss',
    'summary': 'Real-time refresh and desktop notifications for Odoo17CE Discuss',
    'description': """
        Shows desktop notifications for ALL messages in Discuss channels, not just mentions.
        Messages appear instantly without page reload.
    """,
    'depends': ['mail', 'bus'],  # REMOVED 'discuss' from this list
    'data': [],
    'assets': {
        'web.assets_backend': [
            'discuss_realtime_notify/static/src/js/discuss_bus_listener.js',
        ],
    },
    'installable': True,
    'application': True,
}
