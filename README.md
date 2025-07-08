# PhishSense: Multimodal Phishing Detection in Chat Applications

<div align="center">

![PhishSense](https://img.shields.io/badge/PhishSense-Multimodal_Detection-blue?style=flat-square)
![Chat Integration](https://img.shields.io/badge/Chat_Integration-Real--time_Protection-green?style=flat-square)
![Voice Detection](https://img.shields.io/badge/Voice_Detection-AI_Synthesis_Detection-orange?style=flat-square)

</div>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#technology-stack">Technology Stack</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#citation">Citation</a>
</p>

## Overview

**PhishSense** is an advanced multimodal phishing detection system that integrates seamlessly into real-time chat applications. Built on top of the original PhishIntention framework, PhishSense extends phishing detection capabilities to include **voice message analysis** and **real-time chat protection**, making it the first comprehensive solution for detecting both traditional phishing websites and modern vishing (voice phishing) attacks.

### Key Innovations

- **🔍 Multimodal Detection**: Combines visual (screenshots), textual (HTML), and audio (voice messages) analysis
- **🎤 Voice Phishing Detection**: First implementation combining AI voice synthesis detection with content analysis
- **💬 Real-time Chat Integration**: Seamless phishing protection in messaging applications
- **🤖 Dynamic Brand Recognition**: GPT-4 powered brand detection for unknown brands
- **🛡️ Browser Extension**: Direct browser integration for real-time protection
- **🐳 Microservices Architecture**: Scalable, containerized deployment

## Features

### 1. **Multimodal Phishing Detection**
- **Visual Analysis**: Screenshot-based logo detection and brand matching
- **Textual Analysis**: HTML structure analysis and suspicious pattern detection
- **Voice Analysis**: AI-generated voice detection + content phishing analysis
- **Feature Fusion**: Advanced decision-making combining multiple detection signals

### 2. **Real-time Chat Protection**
- **URL Auto-detection**: Automatically finds URLs in chat messages
- **Security Icons**: Visual indicators for suspicious links
- **One-click Scanning**: Instant phishing analysis with detailed results
- **Group Protection**: Protects entire chat groups from malicious links





## Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   React Frontend│    │  Golang Backend │    │Phishing Detection│
│   (Chat UI)     │◄──►│  (WebSocket)    │◄──►│  (PhishSense)    │
└─────────────────┘    └─────────────────┘    └──────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MySQL DB      │    │   MySQL DB      │    │  PhishSense     │
│   (User Data)   │    │   (Chat Data)   │    │  Components:    │
└─────────────────┘    └─────────────────┘    │  • Image Branch │
                                              │  • Text Branch  │
                                              │  • Voice Branch │
                                              │  (RawNet + GPT) │
                                              └─────────────────┘
```

### Detection Pipeline

<img src="big_pic/Multimodal workflow.png" alt="PhishSense Multimodal Workflow" style="width:100%;max-width:800px"/>

**Brief Workflow of PhishSense:**

1. **Input Processing**: URL, screenshot, or voice file
2. **PhishSense Multimodal Analysis**:
   - **Image Branch**: Logo detection → Brand matching → CRP classification
   - **Text Branch**: HTML analysis → Suspicious pattern detection
   - **Voice Branch**: AI synthesis detection + Content analysis (added for chat app)
3. **Feature Fusion**: Advanced decision-making algorithm combining all three modalities
4. **Result Output**: Phishing/Benign classification with confidence scores



## Installation

### Manual Installation

#### 1. Backend Services

```bash
# Start Python phishing detection service
python start_backend.py

# Start Golang chat backend
cd Realtime-chat-app-golang
go run cmd/main.go
```

#### 2. PhishSense Model

```bash
# Start the PhishSense multimodal detection model
python main.py
```

#### 3. Frontend

```bash
# Start React chat application
cd Realtime-chat-app-react-ui
npm install
npm start
```



## Usage

### Chat Application

1. **Login** to the chat application at `http://localhost:3000`
2. **Send messages** containing URLs or voice messages
3. **Look for security icons** (🛡️) next to messages with links or voice content
4. **Click the icon** to trigger PhishSense detection:
   - **For URLs**: Automatically detects the link and uses PhishSense image/text analysis
   - **For Voice Messages**: Triggers PhishSense voice branch for AI synthesis and content analysis
5. **Review results** with detailed analysis breakdown

### Additional Implementation

I have also created a Chrome extension that integrates the PhishSense model for real-time website scanning, providing browser-based phishing protection using the image and text analysis capabilities.

## API Endpoints

### Phishing Detection
- `POST /scan` - Scan website for phishing
- `POST /scan_voice` - Analyze voice file for phishing
- `GET /health` - Service health check

### Chat Backend

**User Management**
- `POST /user/register` - Register a new user
- `POST /user/login` - Login with existing credentials
- `PUT /user` - Modify user information
- `GET /user/:uuid` - Get user details by UUID
- `GET /user/name` - Get user or group by name

**Friend Management**
- `POST /friend` - Add a friend

**Group Management**
- `POST /group/:uuid` - Save group details
- `POST /group/join/:userUuid/:groupUuid` - Join a group

**File Management**
- `POST /file` - Upload a file (e.g., avatar)

**Messaging**
- `GET /message` - Get messages

**WebSocket**
- `/socket.io` - WebSocket connection for real-time communication

## Research Foundation

### Original PhishIntention Framework

This project builds upon the **PhishIntention** framework from the USENIX Security 2022 paper:

**Citation:**
```bibtex
@inproceedings{liu2022inferring,
  title={Inferring Phishing Intention via Webpage Appearance and Dynamics: A Deep Vision Based Approach},
  author={Liu, Ruofan and Lin, Yun and Yang, Xianglin and Ng, Siang Hwee and Divakaran, Dinil Mon and Dong, Jin Song},
  booktitle={30th $\{$USENIX$\}$ Security Symposium ($\{$USENIX$\}$ Security 21)},
  year={2022}
}
```

**Repository:** [https://github.com/lindsey98/PhishIntention](https://github.com/lindsey98/PhishIntention)



### Chat Application Foundation

The chat application is built upon the **Realtime Chat Application** project:

**Features from Original:**
- Real-time messaging with WebSockets
- Media support (text, images, voice, video messages)
- Screen sharing and video chat using WebRTC
- User management (register, login, profile management)

**Frontend Repository:** [https://github.com/Joakim-animate90/Realtime-chat-app-react-ui](https://github.com/Joakim-animate90/Realtime-chat-app-react-ui)

**Backend Repository:** [https://github.com/Joakim-animate90/Realtime-chat-app-golang](https://github.com/Joakim-animate90/Realtime-chat-app-golang)

**Demo Video:** [https://www.loom.com/share/e29f600a5bdb421f9c082ff4d86ae4aa](https://www.loom.com/share/e29f600a5bdb421f9c082ff4d86ae4aa)

## Key Technologies

### Core Technologies
- **React & Redux**: Frontend framework and state management
- **Go & Gin**: Backend server and web framework
- **MySQL**: Database for user and chat data
- **WebSockets**: Real-time communication

### AI/ML (PhishSense)
- **PyTorch**: Deep learning framework
- **RawNet**: Voice synthesis detection
- **Siamese Networks**: Logo/brand matching
- **GPT-4**: Dynamic content analysis
- **Whisper**: Speech recognition

### Infrastructure
- **Docker**: Containerized deployment
- **Nginx**: Reverse proxy
- **WSL**: Windows Subsystem for Linux support

## Contributing

We welcome contributions! Please see our contributing guidelines for details.
