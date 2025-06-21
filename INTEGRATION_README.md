# Phishing Detection Integration in Chat App

This document explains how the phishing detection functionality has been integrated into the real-time chat application.

## Overview

The phishing detection feature has been seamlessly integrated into the chat application, allowing users to scan URLs shared in conversations for potential phishing threats. Instead of using a browser extension, the detection happens directly within the chat interface.

## Features

### 1. **Inline URL Detection**
- Automatically detects URLs in chat messages
- Shows a small security icon next to messages containing links
- Non-intrusive design that doesn't interfere with normal chat flow

### 2. **One-Click Scanning**
- Click the security icon to scan any URL
- Real-time analysis using the same advanced detection algorithms
- Detailed results showing confidence scores and analysis breakdown

### 3. **Visual Feedback**
- Clear visual indicators for safe vs. phishing sites
- Confidence scores and detailed analysis
- Color-coded results (green for safe, red for phishing)

## Architecture

### Backend Integration
- **Golang Backend**: Added `/phish/scan` endpoint that proxies requests to the Python service
- **Python Service**: Runs the original PhishIntention detection algorithms
- **Communication**: HTTP API calls between services

### Frontend Integration
- **SafeComment Component**: Custom comment component that detects URLs and shows scan icons
- **PhishDetector Component**: Modal interface for scanning and displaying results
- **Real-time Updates**: Immediate feedback during scanning process

## How It Works

### 1. **Message Display**
```
User sends: "Check out this link: https://example.com"
↓
SafeComment detects URL in message
↓
Shows security icon next to message
```

### 2. **URL Scanning**
```
User clicks security icon
↓
Opens scan modal with URL
↓
User clicks "Scan Website"
↓
Backend calls Python phishing detection service
↓
Returns detailed analysis results
```

### 3. **Result Display**
```
Shows visual result (safe/phishing)
↓
Displays confidence score
↓
Shows detailed breakdown (image + text analysis)
↓
User can make informed decision
```

## Installation & Setup

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ChromeEx_Phish_Detector
   ```

2. **Start all services**
   ```bash
   docker-compose -f docker-compose-integrated.yml up --build
   ```

3. **Access the application**
   - Chat App: http://localhost:3000
   - Backend API: http://localhost:8888
   - Phishing Detection: http://localhost:5000

### Option 2: Manual Setup

1. **Start the Python phishing detection service**
   ```bash
   cd /path/to/phishing/detection
   python app.py
   ```

2. **Start the Golang chat backend**
   ```bash
   cd Realtime-chat-app-golang
   go run cmd/main.go
   ```

3. **Start the React frontend**
   ```bash
   cd Realtime-chat-app-react-ui
   npm install
   npm start
   ```

## Usage

### For Chat Users

1. **Login to the chat application**
2. **Start a conversation** with friends or join a group
3. **Send or receive messages** containing URLs
4. **Look for the security icon** (🛡️) next to messages with links
5. **Click the icon** to scan the URL
6. **Review the results** and make an informed decision

### Example Workflow

```
Friend: "Hey, check out this amazing deal: https://amazon-deals.com"
↓
[Security icon appears next to message]
↓
You click the security icon
↓
Modal opens: "Scan Website"
↓
Click "Scan Website"
↓
Result: "WARNING: This appears to be a phishing site!"
Confidence: 95.2%
↓
You avoid clicking the malicious link
```

## Technical Details

### API Endpoints

- **POST /phish/scan**: Scan a URL for phishing
  ```json
  {
    "url": "https://example.com"
  }
  ```

- **Response**:
  ```json
  {
    "code": 200,
    "data": {
      "is_phishing": true,
      "confidence": 0.952,
      "details": {
        "image_phish_score": 0.95,
        "text_phish_score": 0.87,
        "image_decision": 1,
        "text_decision": 1
      }
    }
  }
  ```

### Components

- **SafeComment**: Wraps chat messages and adds security icons
- **PhishDetector**: Modal component for scanning and results
- **Backend Proxy**: Golang service that communicates with Python detection

### Security Features

- **Real-time Analysis**: Uses the same advanced algorithms as the Chrome extension
- **Multimodal Detection**: Combines visual and textual analysis
- **Confidence Scoring**: Provides detailed confidence levels
- **Non-intrusive**: Doesn't block or interfere with normal chat usage

## Benefits

1. **Seamless Integration**: No need for browser extensions
2. **Real-time Protection**: Immediate scanning of shared links
3. **User Education**: Shows users why a site is flagged as phishing
4. **Social Protection**: Protects entire chat groups from malicious links
5. **Privacy**: Scanning happens server-side, no data sent to third parties

## Future Enhancements

- **Automatic Scanning**: Scan URLs automatically when shared
- **Whitelist Management**: Allow users to whitelist trusted domains
- **Voice Message Analysis**: Detect AI-generated fake voice messages
- **Group Notifications**: Alert group admins about suspicious links
- **Analytics Dashboard**: Track phishing attempts and patterns

## Troubleshooting

### Common Issues

1. **Scan button not appearing**
   - Check if the message contains valid URLs
   - Ensure the frontend is properly connected to backend

2. **Scan fails**
   - Verify the Python phishing detection service is running
   - Check network connectivity between services

3. **Results not loading**
   - Check browser console for errors
   - Verify API endpoints are accessible

### Logs

- **Frontend**: Check browser developer console
- **Backend**: Check Golang service logs
- **Phishing Service**: Check Python Flask logs

## Support

For issues or questions about the integration:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Ensure all services are running properly
4. Verify network connectivity between components 