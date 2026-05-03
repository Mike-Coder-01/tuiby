document.addEventListener("DOMContentLoaded", function () {
    // Tab navigation
    document.querySelectorAll('.dashboard-nav a').forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);

            // Hide all sections 
            document.querySelectorAll('.dashboard-section').forEach(section => {
                section.classList.remove('active');
            });

            // Deactivate all nav items 
            document.querySelectorAll('.dashboard-nav li').forEach(item => {
                item.classList.remove('active');
            });

            // Show target section 
            document.getElementById(targetId).classList.add('active');
            this.parentElement.classList.add('active');
        });
    });
});
