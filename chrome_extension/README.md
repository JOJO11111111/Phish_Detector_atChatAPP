# PhishIntention Chrome Extension

This Chrome extension integrates with the PhishIntention phishing detection system to analyze websites for potential phishing attempts.

## Setup with WSL

### Prerequisites
- Windows 10/11 with WSL (Ubuntu) installed
- Chrome browser on Windows
- Python environment in WSL with all dependencies installed

### Installation Steps

1. **Prepare the Extension Files**
   - Copy the entire `chrome_extension` folder to a Windows-accessible location:
     ```
     cp -r /path/to/PhishIntention_CyberTest/chrome_extension /mnt/c/Users/YourUsername/PhishIntention_Extension
     ```

2. **Start the Backend Service in WSL**
   - Open a WSL terminal
   - Navigate to the PhishIntention directory:
     ```
     cd /path/to/PhishIntention_CyberTest
     ```
   - Activate your Python environment:
     ```
     source venv/bin/activate  # or your environment activation command
     ```
   - Start the Flask backend:
     ```
     python app.py
     ```
   - The backend should be running on `http://localhost:5000`

3. **Load the Extension in Chrome**
   - Open Chrome on Windows (not in WSL)
   - Go to `chrome://extensions/`
   - Enable "Developer mode" in the top right
   - Click "Load unpacked"
   - Select the Windows directory where you copied the extension files
   - The extension should now appear in your Chrome toolbar

### Usage

1. Click the PhishIntention extension icon in your Chrome toolbar
2. The extension will check if the backend is available
3. If the backend is running, you'll see a prompt asking if you want to scan the current website
4. Click "Scan Website" to analyze the current page
5. Results will be displayed in the popup

### Troubleshooting

- **Backend Not Available**: Make sure the Flask backend is running in WSL
- **Connection Errors**: Verify that the backend is accessible at `http://localhost:5000`
- **Analysis Failures**: Check the WSL terminal for error messages from the backend

## Development

- The extension communicates with the backend via HTTP requests
- The backend runs the PhishIntention detection system on URLs provided by the extension
- Results are returned to the extension and displayed in the popup 