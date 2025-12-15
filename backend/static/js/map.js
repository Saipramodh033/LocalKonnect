/**
 * Map.js - Leaflet map functionality for contractor search
 */

let map = null;
let markers = null;

/**
 * Initialize the contractor search map
 * @param {string} containerId - ID of the map container element
 * @param {Array} contractors - Array of contractor data objects
 */
function initContractorMap(containerId, contractors) {
    // Initialize map centered on user location or default
    map = L.map(containerId).setView([40.7128, -74.0060], 12); // Default to NYC
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Initialize marker cluster group
    markers = L.markerClusterGroup({
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
        maxClusterRadius: 50
    });
    
    // Add contractors to map
    if (contractors && contractors.length > 0) {
        addContractorsToMap(contractors);
        
        // Fit map to show all markers
        const bounds = markers.getBounds();
        if (bounds.isValid()) {
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }
    
    // Try to get user's current location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const userLat = position.coords.latitude;
            const userLng = position.coords.longitude;
            
            // Add user location marker
            L.marker([userLat, userLng], {
                icon: L.divIcon({
                    className: 'user-location-marker',
                    html: '<div class="w-4 h-4 bg-blue-600 rounded-full border-2 border-white shadow-lg"></div>',
                    iconSize: [16, 16]
                })
            }).addTo(map).bindPopup('Your Location');
            
            // Center map on user if no contractors
            if (!contractors || contractors.length === 0) {
                map.setView([userLat, userLng], 13);
            }
        }, function(error) {
            console.log('Geolocation error:', error);
        });
    }
}

/**
 * Add contractors as markers to the map
 * @param {Array} contractors - Array of contractor data
 */
function addContractorsToMap(contractors) {
    contractors.forEach(function(contractor) {
        if (contractor.latitude && contractor.longitude) {
            // Determine marker color based on trust score
            let markerColor;
            if (contractor.trust_score >= 60) {
                markerColor = '#10B981'; // Green
            } else if (contractor.trust_score >= 20) {
                markerColor = '#F59E0B'; // Yellow
            } else {
                markerColor = '#EF4444'; // Red
            }
            
            // Create custom marker icon
            const markerIcon = L.divIcon({
                className: 'contractor-marker',
                html: `
                    <div class="relative">
                        <div class="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold shadow-lg transform hover:scale-110 transition-transform cursor-pointer"
                             style="background-color: ${markerColor}">
                            ${Math.round(contractor.trust_score)}
                        </div>
                    </div>
                `,
                iconSize: [48, 48],
                iconAnchor: [24, 24],
                popupAnchor: [0, -24]
            });
            
            // Create marker
            const marker = L.marker([contractor.latitude, contractor.longitude], {
                icon: markerIcon
            });
            
            // Create popup content
            const popupContent = `
                <div class="p-2 min-w-[250px]">
                    <h3 class="font-bold text-lg mb-2">
                        ${contractor.business_name || contractor.name}
                        ${contractor.is_verified ? '<i class="fas fa-check-circle text-blue-600 ml-1"></i>' : ''}
                    </h3>
                    <p class="text-gray-600 mb-2">
                        <i class="fas fa-briefcase mr-1"></i> ${contractor.service_name}
                    </p>
                    <div class="flex items-center mb-2">
                        <div class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold mr-2"
                             style="background-color: ${markerColor}">
                            ${Math.round(contractor.trust_score)}
                        </div>
                        <div class="text-sm">
                            <div class="font-semibold">Trust Score</div>
                            <div class="text-gray-500">${contractor.total_trust_marks} marks</div>
                        </div>
                    </div>
                    ${contractor.years_of_experience > 0 ? `
                        <p class="text-sm text-gray-600 mb-2">
                            ${contractor.years_of_experience} years experience
                        </p>
                    ` : ''}
                    ${contractor.distance ? `
                        <p class="text-sm text-gray-500 mb-3">
                            <i class="fas fa-map-marker-alt mr-1"></i> ${contractor.distance.toFixed(1)} km away
                        </p>
                    ` : ''}
                    <a href="/contractor/${contractor.id}/" 
                       class="block text-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                        View Profile
                    </a>
                </div>
            `;
            
            marker.bindPopup(popupContent, {
                maxWidth: 300,
                className: 'contractor-popup'
            });
            
            markers.addLayer(marker);
        }
    });
    
    map.addLayer(markers);
}

/**
 * Update contractors on map (for HTMX updates)
 * @param {Array} contractors - New contractor data
 */
function updateMapContractors(contractors) {
    if (markers) {
        markers.clearLayers();
    }
    addContractorsToMap(contractors);
}

/**
 * Center map on specific location
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @param {number} zoom - Zoom level
 */
function centerMap(lat, lng, zoom = 13) {
    if (map) {
        map.setView([lat, lng], zoom);
    }
}
