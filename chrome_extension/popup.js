document.addEventListener('DOMContentLoaded', function () {
  // Get DOM elements
  const permissionSection = document.getElementById('permissionSection');
  const resultSection = document.getElementById('resultSection');
  const urlDisplay = document.getElementById('urlDisplay');
  const scanButton = document.getElementById('scanButton');
  const statusDiv = document.getElementById('status');
  const brandInfoDiv = document.getElementById('brandInfo');
  const confidenceDiv = document.getElementById('confidence');
  const detailsDiv = document.getElementById('details');

  // Backend URL - can be configured for different environments
  const BACKEND_URL = 'http://localhost:5000';

  // Function to check if backend is available
  function checkBackendConnection() {
    return fetch(`${BACKEND_URL}/`)
      .then(response => response.json())
      .then(data => {
        return data.status === 'running';
      })
      .catch(() => {
        return false;
      });
  }

  // Check backend connection on load
  checkBackendConnection().then(isAvailable => {
    if (!isAvailable) {
      scanButton.disabled = true;
      scanButton.textContent = 'Backend Not Available';
      scanButton.title = 'The PhishSense backend service is not running. Please start it in WSL.';
    }
  });

  // Get the current tab
  chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    const currentTab = tabs[0];
    const currentUrl = currentTab.url;

    // Display the current URL
    urlDisplay.textContent = currentUrl;

    // Add click event to scan button
    scanButton.addEventListener('click', function () {
      // Disable the button to prevent multiple clicks
      scanButton.disabled = true;
      scanButton.textContent = 'Scanning...';

      // Hide permission section and show result section
      permissionSection.style.display = 'none';
      resultSection.style.display = 'block';

      // Send URL to backend for analysis
      fetch(`${BACKEND_URL}/scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: currentUrl
        })
      })
        .then(response => {
          if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          if (data.error) {
            statusDiv.textContent = 'Error: ' + data.error;
            statusDiv.className = 'status danger';
            return;
          }

          // Update UI with results
          if (data.is_phishing) {
            statusDiv.textContent = 'WARNING: This appears to be a phishing site!';
            statusDiv.className = 'status danger';
          } else {
            statusDiv.textContent = 'This site appears to be safe';
            statusDiv.className = 'status safe';
          }

          confidenceDiv.textContent = `Confidence: ${(data.confidence * 100).toFixed(1)}%`;

          // Display additional details if available
          if (data.details) {
            let detailsHtml = '<h4>Analysis Details:</h4>';

            // Add image analysis details
            detailsHtml += `<p><strong>Image Analysis:</strong></p>`;
            detailsHtml += `<p>Phish Score: ${(data.details.image_phish_score * 100).toFixed(1)}%</p>`;
            detailsHtml += `<p>Decision: ${data.details.image_decision === 1 ? 'Phishing' : 'Benign'}</p>`;

            // Add text analysis details
            detailsHtml += `<p><strong>Text Analysis:</strong></p>`;
            detailsHtml += `<p>Phish Score: ${(data.details.text_phish_score * 100).toFixed(1)}%</p>`;
            detailsHtml += `<p>Decision: ${data.details.text_decision === 1 ? 'Phishing' : 'Benign'}</p>`;

            detailsDiv.innerHTML = detailsHtml;
          }
        })
        .catch(error => {
          statusDiv.textContent = 'Error: Could not connect to detection service';
          statusDiv.className = 'status danger';
          detailsDiv.innerHTML = `<p>Error details: ${error.message}</p>
                                 <p>Make sure the PhishSense backend is running in WSL.</p>`;
          console.error('Error:', error);
        })
        .finally(() => {
          // Re-enable the scan button
          scanButton.disabled = false;
          scanButton.textContent = 'Scan Website';
        });
    });
  });
}); 