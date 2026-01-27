{
    "name": "Popup Notifications for General Channel", 
    "version": "17.0.1.0.0",
    "category": "Discuss",
    "summary": "Show desktop notifications for #general channel messages",
    "depends": ["mail", "bus"],
    "assets": {
        "web.assets_backend": [
            "popup_notifications/static/src/js/notification_listener.js",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
