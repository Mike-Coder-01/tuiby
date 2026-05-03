document.getElementById('save-profile').addEventListener('click', function() {
    // Profile infos
    const username = document.getElementById('sellerName').value;
    const category = document.getElementById('sellerCategory').value;

    // Location 
    const latitude = document.getElementById('latitude').value;
    const longitude = document.getElementById('longitude').value;
    const location = document.getElementById('sellerLocation').value;

    // Social media handles
    const instagram = document.getElementById('instagram').value;
    const facebook = document.getElementById('facebook').value;
    const tiktok = document.getElementById('tiktok').value;

    // Profile object
    const formData1 = new FormData();
    formData1.append('username', username)

    // Product object
    const formData2 = new FormData();
    formData2.append('category', category)

    // Location object
    const formData3 = new FormData()
    formData3.append('latitude', latitude)
    formData3.append('longitude', longitude)
    location.append('location', location)

    // Social object
    const formData4 = new FormData()
    formData4.append('instagram', instagram)
    formData4.append('facebook', facebook)
    formData4.append('tiktok', tiktok)

    // fetch('', {
    //     'method':'POST',
    //     'body':formData1
    // });

    // fetch('', {
    //     'method':'POST',
    //     'body':formData2
    // });

    // fetch('/update-location/', {
    //     'method':'POST',
    //     'body':formData3
    // });

    fetch('/add-social-handle/', {
        'method':'POST',
        'body':formData4,
    })
    .then(response => response.json())
    .then(data => {
        const messageBox = document.getElementById('messageBox');
        if(data.message) {
            messageBox.innerHTML= data.message;
            messageBox.style.color ='green';
        } else if (data.error) {
            messageBox.innerHTML = data.error;
            messageBox.style.color = 'red';
        }
    })
    .catch(error => {
        document.getElementById('messageBox').innerHTML = 'An error occured';
    });
})