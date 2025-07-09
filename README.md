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

**PhishSense** is a multimodal phishing detection model i made for a LLM + security challenge, it extends phishing detection capabilities to include two branches: image and html branches. In this project, I added one more branch: **voice message analysis**, and integrated this model as a demo about **real-time chat protection**, making it a comprehensive solution for detecting both traditional phishing websites and modern vishing (voice phishing) attacks.

### Key Innovations

- **Multimodal Detection**: Visual (screenshots) + Textual (HTML) analysis: GPT-4 powered brand detection for content understanding and updated logo recognition.
And additionally with audio (voice messages) analysis(**Voice Phishing Detection**): combined AI voice synthesis detection with content analysis provided by LLM
- **Real-time Chat Integration**: V/Phishing protection in messaging applications
- **Microservices Architecture**: Scalable, containerized deployment

## Features

### 1. **Multimodal Phishing Detection**
- **Visual Analysis**: Screenshot-based logo detection and brand matching
- **Textual Analysis**: HTML structure analysis and suspicious pattern detection
- **Voice Analysis**: AI-generated voice detection + content phishing analysis
- **Feature Fusion**: Decision-making by combining multiple detection signals

### 2. **Real-time Chat Protection**
- **URL/Voice Auto-detection**: Automatically finds URLs/voice in chat messages
- **Security Icons**: Click on a visual indicator and start detecting suspicious content
- **One-click Scanning**: Instant phishing analysis with detailed results





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
3. **Feature Fusion & Result Output**: Combine all three modalities and output a phishing score that decides Phishing/Benign 



## Installation

### Manual Installation

#### 1. Backend Services

```bash
# Start Golang chat backend
cd Realtime-chat-app-golang
make build
./bin/chat
```

#### 2. PhishSense Model

```bash
# Start the PhishSense multimodal detection model
python app.py
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

## Demo

[Demo link will be added here]

## API Endpoints

### Phishing Detection
- `POST /scan` - Scan website for phishing
- `POST /scan_voice` - Analyze voice file for phishing

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

## References

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

### Voice Detection model

For the AI-generated voice detection model, I used the **Synthetic Voice Detection**:

**Citation:**
```bibtex
@inproceedings{sun2023ai,
  title={AI-Synthesized Voice Detection Using Neural Vocoder Artifacts},
  author={Sun, Yuxuan and others},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops},
  year={2023}
}
```

**Repository:** [https://github.com/csun22/Synthetic-Voice-Detection-Vocoder-Artifacts](https://github.com/csun22/Synthetic-Voice-Detection-Vocoder-Artifacts)

### Chat Application

The chat application is built upon the **Realtime Chat Application** project:

**Features from Original:**
- Real-time messaging with WebSockets
- Media support (text, images, voice, video messages)
- Screen sharing and video chat using WebRTC
- User management (register, login, profile management)

**Frontend Repository:** [https://github.com/Joakim-animate90/Realtime-chat-app-react-ui](https://github.com/Joakim-animate90/Realtime-chat-app-react-ui)

**Backend Repository:** [https://github.com/Joakim-animate90/Realtime-chat-app-golang](https://github.com/Joakim-animate90/Realtime-chat-app-golang)



## Key Technologies

### Chat Application Stack
- **Front-end**: React, Redux, Ant Design
- **Back-end**: WebSockets, WebRTC
- **State Management**: Redux
- **Networking**: Axios for HTTP requests
- **Database**: MySQL for user and chat data

### AI/ML (PhishSense)
- **PyTorch**: Deep learning framework
- **RawNet**: Voice synthesis detection
- **Siamese Networks**: Logo/brand matching
- **GPT-4**: Dynamic content analysis
- **Whisper**: Speech recognition

