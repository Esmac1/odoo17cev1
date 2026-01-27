/** @odoo-module **/

import { registry } from "@web/core/registry";

function startDiscussRealtimeService(env) {
    console.log("🔔 Discuss Realtime Notify - Starting service...");
    
    const { bus_service, user, notification, router } = env.services;
    
    // Add safety check for required services
    if (!bus_service) {
        console.error("❌ Bus service not available");
        return;
    }
    if (!user) {
        console.error("❌ User service not available");
        return;
    }

    console.log("✅ All required services available");

    // Subscribe to our channel
    bus_service.addChannel('discuss_general_channel');
    console.log("✅ Subscribed to discuss_general_channel");
    
    // Listen for notifications
    bus_service.on('notification', null, (notifications) => {
        console.log("📢 Raw bus notifications received:", notifications);
        
        notifications.forEach((notif) => {
            const [channel, data] = notif;
            console.log("📢 Processing notification - Channel:", channel, "Data:", data);
            
            if (data.type === 'new_message' && data.is_discuss_channel) {
                console.log("✅ Valid discuss channel message received", data);
                _handleNewMessage(data, env);
            } else {
                console.log("❌ Ignoring notification - wrong type or not discuss channel");
            }
        });
    });

    function _handleNewMessage(data, env) {
        console.log("📨 Handling new message:", data);
        
        // Don't show notification for our own messages
        const currentPartnerId = env.services.user.currentPartnerId;
        console.log("👤 Current partner ID:", currentPartnerId, "Author ID:", data.author_id);
        
        if (data.author_id === currentPartnerId) {
            console.log("❌ Skipping own message");
            return;
        }

        console.log("✅ Showing notification for other user's message");
        _showDesktopNotification(data, env);
    }

    function _showDesktopNotification(data, env) {
        console.log("🔔 Attempting to show desktop notification");
        
        if (!("Notification" in window)) {
            console.log("❌ Desktop notifications not supported");
            _fallbackNotification(data, env);
            return;
        }

        console.log("✅ Desktop notifications supported, permission:", Notification.permission);

        if (Notification.permission === "default") {
            console.log("🔄 Requesting notification permission");
            Notification.requestPermission().then(permission => {
                console.log("✅ Notification permission result:", permission);
                if (permission === "granted") {
                    _createDesktopNotification(data, env);
                } else {
                    _fallbackNotification(data, env);
                }
            });
        } else if (Notification.permission === "granted") {
            console.log("✅ Notification permission already granted");
            _createDesktopNotification(data, env);
        } else {
            console.log("❌ Notification permission denied");
            _fallbackNotification(data, env);
        }
    }

    function _createDesktopNotification(data, env) {
        // Add safety check
        if (!data.record_name || !data.author) {
            console.warn("❌ Invalid notification data:", data);
            return;
        }
        
        const cleanBody = _stripHtml(data.body).substring(0, 100);
        console.log("✅ Creating desktop notification:", data.record_name, data.author, cleanBody);
        
        try {
            const notification = new Notification(`💬 ${data.record_name}`, {
                body: `${data.author}: ${cleanBody}`,
                icon: '/web/static/img/odoo-icon.png',
                tag: `discuss-${data.res_id}`,
                requireInteraction: false,
            });

            notification.onclick = () => {
                console.log("🖱️ Notification clicked, opening channel:", data.res_id);
                window.focus();
                notification.close();
                _openChannel(data.res_id, env);
            };

            setTimeout(() => {
                notification.close();
            }, 5000);
            
            console.log("✅ Desktop notification created successfully");
        } catch (error) {
            console.error("❌ Error creating desktop notification:", error);
            _fallbackNotification(data, env);
        }
    }

    function _fallbackNotification(data, env) {
        console.log("🔄 Using fallback notification");
        const cleanBody = _stripHtml(data.body).substring(0, 100);
        if (env.services.notification) {
            env.services.notification.add(
                `💬 ${data.record_name}: ${data.author} - ${cleanBody}`,
                { 
                    type: 'info',
                    title: 'New Message',
                    sticky: false,
                }
            );
            console.log("✅ Fallback notification shown");
        } else {
            console.error("❌ Notification service not available for fallback");
        }
    }

    function _stripHtml(html) {
        const tmp = document.createElement("DIV");
        tmp.innerHTML = html;
        return tmp.textContent || tmp.innerText || "";
    }

    function _openChannel(channelId, env) {
        if (env.services.router) {
            console.log("🧭 Navigating to channel:", channelId);
            env.services.router.navigate({
                to: '/discuss',
                hash: {
                    mode: 'discuss',
                    channelId: channelId,
                },
            });
        } else {
            console.error("❌ Router service not available");
        }
    }
}

const discussRealtimeService = {
    dependencies: ["bus_service", "user", "notification", "router"],
    start: startDiscussRealtimeService,
};

registry.category("services").add("discuss_realtime_notify", discussRealtimeService);

console.log("🔔 Discuss Realtime Notify - Service registered!");
