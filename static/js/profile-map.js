// Profile map initialization

// Initialize map when Google Maps API is loaded
function initMap() {
    // Get map container
    const mapElement = document.getElementById('map');
    
    // Check if map element exists
    if (!mapElement) return;
    
    // Get location data from data attributes
    const latitude = parseFloat(mapElement.dataset.latitude);
    const longitude = parseFloat(mapElement.dataset.longitude);
    const isOwner = mapElement.dataset.isOwner === 'true';
    
    // Create location object
    const location = { 
        lat: latitude, 
        lng: longitude 
    };
    
    // Create map
    const map = new google.maps.Map(mapElement, {
        zoom: 12,
        center: location,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: true,
        zoomControl: true
    });
    
    // Add marker or circle based on ownership
    if (isOwner) {
        // Exact location marker for the profile owner
        const marker = new google.maps.Marker({
            position: location,
            map: map,
            title: "Your Location",
            animation: google.maps.Animation.DROP
        });
    } else {
        // Create a circle to approximate location for privacy
        const circle = new google.maps.Circle({
            strokeColor: "#007bff",
            strokeOpacity: 0.8,
            strokeWeight: 2,
            fillColor: "#007bff",
            fillOpacity: 0.35,
            map: map,
            center: location,
            radius: 1000 // 1km radius for privacy
        });
    }
} 