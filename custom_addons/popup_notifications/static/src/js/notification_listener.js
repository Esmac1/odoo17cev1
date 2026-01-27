/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

console.log("🔔 GENERAL CHANNEL NOTIFICATIONS - Loading...");

const GeneralChannelNotificationService = {
    dependencies: ["notification", "bus_service"],
    
    start(env, services) {
        console.log("🔔 GENERAL CHANNEL NOTIFICATIONS - Starting service...");
        
        const notificationService = services.notification;
        const busService = services.bus_service;
        
        let generalChannelId = null;
        let processedMessages = new Set();
        
        // Listen to bus notifications
        busService.addEventListener("notification", (event) => {
            handleBusNotification(event.detail || event);
        });
        
        function handleBusNotification(payload) {
            console.log("🔔 Bus notification received:", payload);
            
            // Look for new message notifications
            if (payload && payload.type === 'mail.channel/new_message') {
                const messageData = payload.payload || payload;
                checkIfGeneralChannelMessage(messageData);
            }
            
            // Also check for channel updates that might contain general channel info
            if (payload && (payload.type === 'mail.channel.partner/typing' || payload.type === 'mail.channel/seen')) {
                // This might help us identify the general channel
                discoverGeneralChannel();
            }
        }
        
        function discoverGeneralChannel() {
            // Try to find general channel by scanning the DOM
            const channelElements = document.querySelectorAll('.o_Discuss_sidebar [data-thread-name]');
            for (let element of channelElements) {
                const channelName = element.textContent.toLowerCase();
                if (channelName.includes('general') && element.dataset.threadId) {
                    generalChannelId = parseInt(element.dataset.threadId);
                    console.log("🔔 Found general channel ID:", generalChannelId);
                    break;
                }
            }
        }
        
        function checkIfGeneralChannelMessage(messageData) {
            // If we know the general channel ID, check against it
            if (generalChannelId && messageData.channel_id === generalChannelId) {
                showGeneralNotification(messageData);
                return;
            }
            
            // If we don't know the ID yet, try to discover it
            if (!generalChannelId) {
                discoverGeneralChannel();
                // If we found it now, check again
                if (generalChannelId && messageData.channel_id === generalChannelId) {
                    showGeneralNotification(messageData);
                    return;
                }
            }
            
            // Fallback: check if this looks like a general channel message
            // by looking at the DOM for active channels
            const activeChannel = document.querySelector('.o_Discuss_thread[data-thread-name]');
            if (activeChannel) {
                const activeChannelName = activeChannel.dataset.threadName;
                if (activeChannelName && activeChannelName.toLowerCase().includes('general')) {
                    showGeneralNotification(messageData);
                }
            }
        }
        
        function showGeneralNotification(messageData) {
            const messageId = messageData.id || JSON.stringify(messageData);
            
            // Prevent duplicates
            if (processedMessages.has(messageId)) {
                return;
            }
            processedMessages.add(messageId);
            setTimeout(() => processedMessages.delete(messageId), 10000);
            
            const authorName = messageData.author_name || 'Someone';
            let body = messageData.body || messageData.message || 'New message';
            
            // Clean HTML tags
            body = body.replace(/<[^>]*>/g, '');
            
            // Limit length
            if (body.length > 100) {
                body = body.substring(0, 100) + '...';
            }
            
            console.log(`🔔 GENERAL CHANNEL: ${authorName}: ${body}`);
            
            // Show Odoo notification
            notificationService.add(`${authorName}: ${body}`, {
                title: `#general`,
                type: "info",
                sticky: false,
            });
            
            // Play sound
            playNotificationSound();
            
            // Browser notification as backup
            showBrowserNotification(authorName, body);
        }
        
        function showBrowserNotification(authorName, message) {
            if ("Notification" in window) {
                if (Notification.permission === "granted") {
                    new Notification(`#general - ${authorName}`, {
                        body: message,
                        icon: "/web/static/img/odoo-icon.png"
                    });
                } else if (Notification.permission === "default") {
                    Notification.requestPermission();
                }
            }
        }
        
        function playNotificationSound() {
            try {
                const context = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = context.createOscillator();
                const gainNode = context.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(context.destination);
                
                oscillator.frequency.value = 600;
                oscillator.type = 'sine';
                gainNode.gain.value = 0.1;
                
                oscillator.start();
                setTimeout(() => oscillator.stop(), 150);
            } catch (error) {
                // Ignore audio errors
            }
        }
        
        // Initial discovery
        setTimeout(discoverGeneralChannel, 2000);
        
        // Return control methods
        return {
            rediscover: discoverGeneralChannel,
            getChannelId: () => generalChannelId,
            test: () => {
                showGeneralNotification({
                    author_name: 'Test User', 
                    body: 'This is a test notification for #general channel',
                    id: 'test-' + Date.now()
                });
            }
        };
    }
};

// Register the service
registry.category("services").add("general_channel_notification_service", GeneralChannelNotificationService);

console.log("🔔 GENERAL CHANNEL NOTIFICATIONS - Service registered!");
console.log("🔔 Use GeneralNotify.test() to test notifications");

// Make available globally for testing
setTimeout(() => {
    if (typeof odoo !== 'undefined') {
        odoo.GeneralNotify = registry.category("services").get("general_channel_notification_service");
        console.log("🔔 Global: odoo.GeneralNotify available for testing");
    }
}, 3000);
