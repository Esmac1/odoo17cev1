/** @odoo-module **/

console.log('🚀 NUCLEAR Discuss Notification Plus - Loading...');

(function() {
    'use strict';

    let messageCount = 0;
    let isActive = true;
    const processedMessages = new Set();

    // ==================== NUCLEAR APPROACH ====================
    // Monitor ALL XMLHttpRequest and Fetch requests
    // ===========================================================

    // 1. Intercept XMLHttpRequest
    const originalXHR = window.XMLHttpRequest;
    const XHRInterceptor = function() {
        const xhr = new originalXHR();
        const originalOpen = xhr.open;
        const originalSend = xhr.send;
        
        xhr.open = function(method, url) {
            this._url = url;
            return originalOpen.apply(this, arguments);
        };
        
        xhr.send = function(data) {
            // Check if this is a message-related request
            if (this._url && (
                this._url.includes('/mail/') || 
                this._url.includes('/web/dataset/') ||
                this._url.includes('/discuss/') ||
                this._url.includes('/message/')
            )) {
                this.addEventListener('load', function() {
                    if (this.status === 200 && this.responseText) {
                        try {
                            const response = JSON.parse(this.responseText);
                            scanResponseForMessages(response, this._url);
                        } catch (e) {
                            // Not JSON, try to scan text
                            scanTextForMessages(this.responseText, this._url);
                        }
                    }
                });
            }
            return originalSend.apply(this, arguments);
        };
        
        return xhr;
    };
    window.XMLHttpRequest = XHRInterceptor;

    // 2. Intercept Fetch API
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args).then(response => {
            const url = args[0];
            if (url && (
                url.includes('/mail/') || 
                url.includes('/web/dataset/') ||
                url.includes('/discuss/') ||
                url.includes('/message/')
            )) {
                response.clone().text().then(text => {
                    try {
                        const data = JSON.parse(text);
                        scanResponseForMessages(data, url);
                    } catch (e) {
                        scanTextForMessages(text, url);
                    }
                });
            }
            return response;
        });
    };

    // 3. Monitor WebSocket connections
    const originalWebSocket = window.WebSocket;
    window.WebSocket = function(url, protocols) {
        const ws = new originalWebSocket(url, protocols);
        
        if (url.includes('websocket') || url.includes('longpolling')) {
            const originalOnMessage = ws.onmessage;
            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    scanWebSocketMessage(data);
                } catch (e) {
                    // Not JSON
                }
                if (originalOnMessage) {
                    originalOnMessage.call(this, event);
                }
            };
        }
        
        return ws;
    };

    // ==================== MESSAGE DETECTION ====================

    function scanResponseForMessages(response, url) {
        console.log('🔍 Scanning response from:', url);
        
        if (typeof response === 'object') {
            // Deep scan the object for messages
            deepScanObject(response, url);
        }
    }

    function scanTextForMessages(text, url) {
        // Look for message patterns in plain text
        if (text.includes('o_Message') || text.includes('mail_message') || text.includes('message_content')) {
            console.log('📨 Found message content in:', url);
            // Force DOM scan after a short delay
            setTimeout(forceDOMScan, 1000);
        }
    }

    function scanWebSocketMessage(data) {
        console.log('📡 WebSocket message:', data);
        
        if (data && typeof data === 'object') {
            // Check for message notifications
            if (data.type === 'mail.message/new' || 
                (data.message && data.message.body) ||
                (data.payload && data.payload.body)) {
                handleNewMessage(data);
            }
        }
    }

    function deepScanObject(obj, source) {
        if (!obj || typeof obj !== 'object') return;
        
        // Check for message data in various formats
        if (obj.body || obj.message || obj.preview) {
            console.log('🎯 Found message in object:', source, obj);
            handleNewMessage(obj);
        }
        
        // Recursively scan nested objects
        for (let key in obj) {
            if (obj.hasOwnProperty(key)) {
                deepScanObject(obj[key], source + '.' + key);
            }
        }
    }

    function handleNewMessage(messageData) {
        const messageId = messageData.id || 'msg_' + Date.now();
        
        if (processedMessages.has(messageId)) {
            return;
        }
        processedMessages.add(messageId);
        
        // Extract message info
        const authorName = extractAuthorName(messageData);
        const messageBody = extractMessageBody(messageData);
        const threadName = extractThreadName(messageData);
        
        // Skip if missing critical info
        if (!authorName || authorName === 'Unknown') {
            return;
        }
        
        // Skip own messages if detectable
        if (isOwnMessage(authorName)) {
            return;
        }
        
        messageCount++;
        console.log(`🚀 NOTIFICATION #${messageCount}: ${authorName} in ${threadName}`);
        
        // Show notification
        showNuclearNotification(authorName, messageBody, threadName);
    }

    function extractAuthorName(data) {
        return (data.author_id && data.author_id[1]) ||
               (data.author && data.author.name) ||
               (data.author_name) ||
               (data.partner_id && data.partner_id[1]) ||
               'Unknown';
    }

    function extractMessageBody(data) {
        const body = data.body || data.message || data.preview || data.content || 'New message';
        // Clean HTML tags
        const cleanBody = body.replace(/<[^>]*>/g, '');
        return cleanBody.length > 80 ? cleanBody.substring(0, 80) + '...' : cleanBody;
    }

    function extractThreadName(data) {
        return (data.record_name) ||
               (data.channel_id && data.channel_id[1]) ||
               (data.thread_name) ||
               (data.model === 'mail.channel' ? 'General Channel' : 'Private Chat');
    }

    function isOwnMessage(authorName) {
        // Simple check - you might need to adjust this
        const currentUser = odoo && odoo.session_info && odoo.session_info.username;
        if (currentUser && authorName.includes(currentUser)) {
            return true;
        }
        return false;
    }

    // ==================== NOTIFICATION SYSTEM ====================

    function showNuclearNotification(authorName, messageBody, threadName) {
        console.log(`💥 NUCLEAR NOTIFICATION: ${authorName} in ${threadName}: ${messageBody}`);
        
        // Play sound
        playNotificationSound();
        
        // Show visual notification
        createNuclearNotification(authorName, messageBody, threadName);
        
        // Show browser notification
        showBrowserNotification(authorName, messageBody, threadName);
    }

    function playNotificationSound() {
        try {
            const audio = new Audio('/web/static/src/sounds/notification.mp3');
            audio.volume = 0.7;
            audio.play().catch(() => {
                // Fallback beep
                playBeep();
            });
        } catch (error) {
            playBeep();
        }
    }

    function playBeep() {
        try {
            const context = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = context.createOscillator();
            const gainNode = context.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(context.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            gainNode.gain.setValueAtTime(0.3, context.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + 0.5);
            
            oscillator.start(context.currentTime);
            oscillator.stop(context.currentTime + 0.5);
        } catch (error) {
            // Silent fail
        }
    }

    function createNuclearNotification(authorName, messageBody, threadName) {
        const notification = document.createElement('div');
        notification.className = 'nuclear-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ff0000;
            box-shadow: 0 4px 20px rgba(255, 0, 0, 0.3);
            z-index: 99999;
            max-width: 350px;
            font-family: system-ui, -apple-system, sans-serif;
            animation: nuclearSlideIn 0.4s ease-out;
        `;

        notification.innerHTML = `
            <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px;">💥 ${threadName}</div>
            <div style="font-size: 14px; margin-bottom: 6px;"><strong>${authorName}:</strong></div>
            <div style="font-size: 13px; opacity: 0.9;">${messageBody}</div>
            <div style="font-size: 10px; opacity: 0.7; margin-top: 8px; text-align: right;">Nuclear Detection</div>
        `;

        document.body.appendChild(notification);

        // Remove after 6 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 6000);
    }

    function showBrowserNotification(authorName, messageBody, threadName) {
        if (!('Notification' in window)) return;

        if (Notification.permission === 'granted') {
            new Notification(`💥 ${authorName} - ${threadName}`, {
                body: messageBody,
                icon: '/web/static/src/img/odoo_o.png',
                tag: 'nuclear-notification'
            });
        } else if (Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    new Notification(`💥 ${authorName} - ${threadName}`, {
                        body: messageBody,
                        icon: '/web/static/src/img/odoo_o.png'
                    });
                }
            });
        }
    }

    // ==================== BACKUP SYSTEMS ====================

    function forceDOMScan() {
        console.log('🔍 FORCE SCANNING DOM FOR MESSAGES...');
        const messages = document.querySelectorAll('.o_Message');
        console.log(`🔍 Found ${messages.length} messages in DOM`);
        
        messages.forEach(msg => {
            if (!msg.dataset.nuclearScanned) {
                msg.dataset.nuclearScanned = 'true';
                const author = msg.querySelector('.o_Message_author, .o_Message_authorName');
                const content = msg.querySelector('.o_Message_content, .o_Message_body');
                
                if (author && content) {
                    const authorName = author.textContent.trim();
                    const messageBody = content.textContent.trim().substring(0, 80) + '...';
                    const threadElement = msg.closest('.o_ThreadView');
                    const threadName = threadElement ? 
                        (threadElement.querySelector('.o_ThreadView_header')?.textContent.trim() || 'General Channel') : 
                        'General Channel';
                    
                    if (!isOwnMessage(authorName)) {
                        messageCount++;
                        console.log(`🔍 DOM MESSAGE #${messageCount}: ${authorName} in ${threadName}`);
                        showNuclearNotification(authorName, messageBody, threadName);
                    }
                }
            }
        });
    }

    // Periodic DOM scanning as backup
    setInterval(forceDOMScan, 3000);

    // ==================== DEBUG & CONTROLS ====================

    // Add CSS for animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes nuclearSlideIn {
            from {
                transform: translateX(100%) scale(0.8);
                opacity: 0;
            }
            to {
                transform: translateX(0) scale(1);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);

    // Global controls
    window.NuclearNotify = {
        test: () => {
            showNuclearNotification('Test User', 'This is a NUCLEAR test notification! Should work for ALL messages!', 'General Channel');
            return `Test sent! Total notifications: ${messageCount}`;
        },
        scan: () => {
            forceDOMScan();
            return `DOM scan complete. Total: ${messageCount}`;
        },
        status: () => {
            return {
                active: isActive,
                totalNotifications: messageCount,
                processedMessages: processedMessages.size,
                permission: Notification.permission
            };
        },
        enable: () => { isActive = true; return 'Enabled'; },
        disable: () => { isActive = false; return 'Disabled'; }
    };

    console.log('💥 NUCLEAR Discuss Notification Plus - READY!');
    console.log('💥 Commands: NuclearNotify.test(), NuclearNotify.status()');

})();
