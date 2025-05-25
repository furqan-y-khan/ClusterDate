// Firebase Cloud Messaging integration

// Initialize Firebase with app configuration
const firebaseConfig = {
    apiKey: FIREBASE_CONFIG.apiKey,
    authDomain: FIREBASE_CONFIG.authDomain,
    projectId: FIREBASE_CONFIG.projectId,
    storageBucket: FIREBASE_CONFIG.storageBucket,
    messagingSenderId: FIREBASE_CONFIG.messagingSenderId,
    appId: FIREBASE_CONFIG.appId,
    measurementId: FIREBASE_CONFIG.measurementId
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Request permission and get token
async function initializeMessaging() {
    try {
        // Request permission
        const permission = await Notification.requestPermission();
        
        if (permission === 'granted') {
            console.log('Notification permission granted.');
            
            // Get registration token
            const token = await messaging.getToken({
                vapidKey: WEBPUSH_VAPID_PUBLIC_KEY
            });
            
            if (token) {
                console.log('FCM token:', token);
                // Send the token to the server
                await updateFcmToken(token);
            } else {
                console.log('No registration token available.');
            }
            
            // Handle token refresh
            messaging.onTokenRefresh(async () => {
                try {
                    const refreshedToken = await messaging.getToken({
                        vapidKey: WEBPUSH_VAPID_PUBLIC_KEY
                    });
                    console.log('Token refreshed:', refreshedToken);
                    // Send the refreshed token to the server
                    await updateFcmToken(refreshedToken);
                } catch (err) {
                    console.error('Unable to retrieve refreshed token:', err);
                }
            });
        } else {
            console.warn('Notification permission denied.');
        }
    } catch (err) {
        console.error('Error getting permission or token:', err);
    }
}

// Send token to the server
async function updateFcmToken(token) {
    try {
        const response = await fetch('/accounts/update-fcm-token/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ token })
        });
        
        if (response.ok) {
            console.log('FCM token updated successfully.');
        } else {
            console.error('Failed to update FCM token:', response.statusText);
        }
    } catch (err) {
        console.error('Error updating FCM token:', err);
    }
}

// Handle foreground messages
messaging.onMessage((payload) => {
    console.log('Foreground message received:', payload);
    
    // Extract notification data
    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: '/static/images/logo.png',
        badge: '/static/images/badge.png',
        data: payload.data
    };
    
    // Show notification if the browser supports it
    if ('Notification' in window && Notification.permission === 'granted') {
        navigator.serviceWorker.ready
            .then(registration => {
                registration.showNotification(notificationTitle, notificationOptions);
            })
            .catch(err => {
                console.error('Error showing notification:', err);
            });
    }
    
    // Update notifications counter
    updateNotificationCounter();
});

// Update the notifications counter in the UI
function updateNotificationCounter() {
    fetch('/messaging/notifications/count/')
        .then(response => response.json())
        .then(data => {
            const notificationCounter = document.getElementById('notification-counter');
            if (notificationCounter) {
                notificationCounter.textContent = data.count;
                notificationCounter.style.display = data.count > 0 ? 'inline-flex' : 'none';
            }
        })
        .catch(err => {
            console.error('Error fetching notification count:', err);
        });
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize messaging when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Check if Firebase is available
    if (typeof firebase !== 'undefined' && firebase.messaging) {
        initializeMessaging();
        
        // Update notification counter initially
        updateNotificationCounter();
        
        // Update notification counter periodically
        setInterval(updateNotificationCounter, 60000); // Every minute
    }
}); 