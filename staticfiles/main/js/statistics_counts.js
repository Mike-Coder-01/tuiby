// Function to get CSRF token from the hidden input field
function getCSRFTokenFromInput() {
    const csrfInput = document.getElementById('csrf_token_input');
    return csrfInput ? csrfInput.value : '';
}


// Function to send handle ID to backend
function getHandleId(handle_id) {
    const csrfToken = getCSRFTokenFromInput();

    fetch('/update-statistics/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ handle_id: handle_id })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Server response:", data);
    })
    .catch(error => {
        console.error("Error sending handle ID:", error);
    });
}

