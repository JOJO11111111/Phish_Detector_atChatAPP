# Setup Guide: Integrated Phishing Detection

## Quick Start

### 1. Start the Backend Service

```bash
# In the main project directory
python start_backend.py
```

This will start the Flask service at `http://localhost:5000`

### 2. Start the Chat App Frontend

```bash
# In the React app directory
cd Realtime-chat-app-react-ui
npm install
npm start
```

This will start the React app at `http://localhost:3000`

### 3. Test the Integration

1. **Login to the chat app**
2. **Send a message with a URL** (e.g., "Check this: https://tiffanybao-for-phishing-simulation.netlify.app/")
3. **Click the security icon** (🛡️) next to the message
4. **Choose detection mode**:
   - Auto-detect URLs in message
   - Manually enter URL to check
5. **Click "Detect Phishing"**
6. **Wait for analysis** (takes 10-30 seconds)
7. **View results** in the popup modal

## How It Works

### Backend Workflow:
1. **Receive URL** from frontend
2. **Crawl website** using Selenium WebDriver
3. **Save HTML** and **screenshot**
4. **Run PhishIntention analysis**:
   - Image analysis (logo detection, brand matching)
   - Text analysis (HTML structure, suspicious patterns)
   - Feature fusion and decision making
5. **Return results** to frontend

### Frontend Workflow:
1. **Detect URLs** in chat messages
2. **Show security icon** next to messages with links
3. **Open scan modal** when icon is clicked
4. **Send URL** to backend for analysis
5. **Display results** in popup modal

## Expected Results

### For Phishing Sites:
- **Red warning icon** ⚠️
- **"WARNING: This appears to be a phishing site!"**
- **High confidence score** (e.g., 95.2%)
- **Detailed analysis breakdown**

### For Safe Sites:
- **Green checkmark** ✅
- **"This site appears to be safe"**
- **Lower confidence score**
- **Detailed analysis breakdown**

## Troubleshooting

### Backend Issues:
- **Port 5000 in use**: Change port in `start_backend.py`
- **Chrome WebDriver issues**: Install Chrome and ChromeDriver
- **Model loading errors**: Check if model files exist in `./models/`

### Frontend Issues:
- **CORS errors**: Backend should allow CORS (already configured)
- **Connection refused**: Make sure backend is running on port 5000
- **No security icons**: Check browser console for errors

### Common Issues:
1. **"Failed to crawl website"**: Website might be blocking automated access
2. **"No results found"**: Analysis might have failed, check backend logs
3. **"Connection refused"**: Backend service not running

## Test URLs

### Known Phishing Sites (for testing):
- `https://tiffanybao-for-phishing-simulation.netlify.app/`
- Any other phishing simulation sites

### Safe Sites (for testing):
- `https://google.com`
- `https://github.com`
- `https://stackoverflow.com`

## Logs

### Backend Logs:
- Check terminal where `start_backend.py` is running
- Look for crawling, analysis, and error messages

### Frontend Logs:
- Open browser developer console (F12)
- Check for network requests and errors

## Next Steps

1. **Voice Analysis**: Implement AI voice detection
2. **Auto-scanning**: Scan URLs automatically when shared
3. **Whitelist**: Allow users to whitelist trusted domains
4. **Analytics**: Track phishing attempts and patterns 