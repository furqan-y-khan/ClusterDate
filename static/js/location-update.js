// Location update JavaScript

// Update user's location periodically
document.addEventListener('DOMContentLoaded', function() {
    // Check if the user is logged in
    if (document.body.classList.contains('logged-in')) {
        // Get current location and update
        updateLocation();
        
        // Update location every 15 minutes
        setInterval(updateLocation, 15 * 60 * 1000);
    }
});

// Get current location and send to server
function updateLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            // Success callback
            function(position) {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                
                // Send to server
                sendLocationToServer(latitude, longitude);
            },
            // Error callback
            function(error) {
                console.error('Error getting location:', error.message);
            },
            // Options
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    } else {
        console.error('Geolocation is not supported by this browser.');
    }
}

// Send location to server
function sendLocationToServer(latitude, longitude) {
    fetch('/core/update-location/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            latitude: latitude,
            longitude: longitude
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Location updated successfully:', data.location);
        } else {
            console.error('Failed to update location:', data.error);
        }
    })
    .catch(error => {
        console.error('Error sending location:', error);
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