document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('camera-search');
    const resultsContainer = document.getElementById('autocomplete-results');
    const detectBtn = document.getElementById('detect-btn');
    const resultImage = document.getElementById('result-image');
    const loader = document.getElementById('loader');
    const errorMessage = document.getElementById('error-message');
    const detectionMessage = document.getElementById('detection-message');

    let selectedCameraId = null;
    let debounceTimer;

    // --- Autocomplete Logic ---
    searchInput.addEventListener('input', () => {
        const query = searchInput.value;
        
        // Clear previous results and cancel previous timer
        resultsContainer.innerHTML = '';
        clearTimeout(debounceTimer);

        if (query.length < 2) {
            hideAutocomplete();
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch(`/get_camera_names?query=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    displayAutocomplete(data);
                })
                .catch(error => console.error('Error fetching cameras:', error));
        }, 300); // 300ms debounce
    });

    function displayAutocomplete(items) {
        if (items.length === 0) {
            hideAutocomplete();
            return;
        }
        resultsContainer.innerHTML = '';
        items.forEach(item => {
            const div = document.createElement('div');
            div.textContent = item.name;
            div.classList.add('autocomplete-item');
            div.addEventListener('click', () => {
                searchInput.value = item.name;
                selectedCameraId = item.id;
                hideAutocomplete();
                detectBtn.disabled = false;
            });
            resultsContainer.appendChild(div);
        });
        resultsContainer.style.display = 'block';
    }

    function hideAutocomplete() {
        resultsContainer.style.display = 'none';
    }

    // Hide autocomplete when clicking outside
    document.addEventListener('click', (e) => {
        if (e.target !== searchInput && e.target.parentNode !== resultsContainer) {
            hideAutocomplete();
        }
    });


    // --- Detection Logic ---
    detectBtn.addEventListener('click', () => {
        if (!selectedCameraId) {
            showError("Please select a valid camera from the list.");
            return;
        }
        
        showLoader(true);
        hideError();
        resultImage.style.display = 'none';
        detectionMessage.style.display = 'none';

        const startTime = Date.now();
        fetch(`/detect_parking?camera_id=${selectedCameraId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok (status: ${response.status})`);
                }
                // Get the count from the custom header
                const spotCount = parseInt(response.headers.get('X-Open-Spots-Count'), 10);
                displayDetectionMessage(spotCount);

                return response.blob();
            })
            .then(imageBlob => {
                const imageUrl = URL.createObjectURL(imageBlob);
                resultImage.src = imageUrl;
                resultImage.style.display = 'block';
                const duration = Date.now() - startTime;
                console.log(`Image processed and displayed in ${duration}ms.`);
            })
            .catch(error => {
                console.error('Detection error:', error);
                showError("Failed to get detection results. The camera may be offline.");
            })
            .finally(() => {
                showLoader(false);
            });
    });


    // --- UI Helper Functions ---
    function showLoader(show) {
        loader.style.display = show ? 'block' : 'none';
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }

    function displayDetectionMessage(count) {
        if (isNaN(count)) {
            detectionMessage.style.display = 'none';
            return;
        }

        if (count === 0) {
            detectionMessage.textContent = 'No Open Parking Detected';
            detectionMessage.className = 'detection-message no-spots';
            detectionMessage.style.display = 'block';
        } else {
            // If spots are found, just hide the message.
            detectionMessage.style.display = 'none';
        }
    }

    // Initially disable the button
    detectBtn.disabled = true;
}); 