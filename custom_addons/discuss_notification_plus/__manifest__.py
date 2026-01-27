{
    'name': 'Discuss Notification Plus',
    'version': '17.0.1.0.0',
    'category': 'Discuss',
    'summary': 'Desktop notifications for ALL messages',
    'depends': ['mail'],
    'assets': {
        'web.assets_backend': [
            'discuss_notification_plus/static/src/js/discuss_notification.js',
        ],
    },
    'installable': True,
    'application': False,
}
