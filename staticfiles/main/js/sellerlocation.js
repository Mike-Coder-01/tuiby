// Get location when user clicks the button
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                let lat = position.coords.latitude;
                let lon = position.coords.longitude;

                // Save to localStorage
                localStorage.setItem("latitude", lat);
                localStorage.setItem("longitude", lon);

                // Set hidden inputs
                document.getElementById("latitude").value = lat;
                document.getElementById("longitude").value = lon;

                // Get location name
                getLocationName(lat, lon);
            },
            function (error) {
                alert("Error getting location: " + error.message);
            }
        );
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}

// Get location name (city or town) from OpenStreetMap's Nominatim service
function getLocationName(lat, lon) {
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`)
        .then(response => response.json())
        .then(data => {
            let city = data.address.city || data.address.town || data.address.village || data.address.municipality || 'City not found';

            // Save city in localStorage
            localStorage.setItem("city", city);

            // Set input value
            document.getElementById("seller-Location").value = city;
        })
        .catch(error => console.error('Error:', error));
}

// Form submission validation to ensure location is fetched
document.querySelector("#locationForm").addEventListener("submit", function(event) {
    const location = document.getElementById("seller-Location").value;
    
    // Check if location is empty, and prevent form submission if not filled
    if (!location) {
        alert("Please allow the location to be fetched before submitting the form.");
        event.preventDefault(); // Prevent form submission
    }
});

// Load saved location when the page is loaded
document.addEventListener("DOMContentLoaded", function () {
    const savedCity = localStorage.getItem("city");
    const savedLat = localStorage.getItem("latitude");
    const savedLon = localStorage.getItem("longitude");

    // If saved location exists in localStorage, pre-fill the fields
    if (savedCity && savedLat && savedLon) {
        document.getElementById("seller-Location").value = savedCity;
        document.getElementById("latitude").value = savedLat;
        document.getElementById("longitude").value = savedLon;
    }
});
