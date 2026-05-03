// Search Form Submission
const searchForm = document.getElementById('searchForm');
if(searchForm) {
    searchForm.addEventListener('submit', function(e){
        e.preventDefault();

        // Get longitude and latitudes
        // Get form values
        const platform = document.getElementById('platform').value;
        const location = document.getElementById('location').value;
        let query = document.getElementById("searchTerm").value.trim();
        if (!query) {
            alert("Please enter a search term.");
            return;
        }

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function (position) {
                    let latitude = position.coords.latitude;
                    let longitude = position.coords.longitude;

                    // Redirect with query and location
                    let searchUrl = `/filter_sellers/?query=${encodeURIComponent(query)}&platform=${platform}&location=${location}&latitude=${latitude}&longitude=${longitude}`;
                    window.location.href = searchUrl;
                },
                function (error) {
                    alert("Location access denied. Please allow location services.");
                }
            );
        } else {
            alert("Geolocation is not supported by your browser.");
        }

   })
}