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

### 3. **Voice Phishing Detection**
- **AI Voice Detection**: Uses RawNet model to detect synthetic/AI-generated voices
- **Content Analysis**: GPT-4 integration to analyze voice content for phishing indicators
- **Real-time Processing**: Can analyze voice files uploaded through chat interface
- **Multimodal Voice Analysis**: Combines AI detection + content analysis



## Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  Golang Backend │    │ Python Detection│
│   (Chat UI)     │◄──►│  (WebSocket)    │◄──►│  (PhishSense)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  Golang Backend │    │  PhishSense     │
│   (Chat UI)     │◄──►│  (WebSocket)    │◄──►│  Components:    │
└─────────────────┘    └─────────────────┘    │  • Image Branch │
                                              │  • Text Branch  │
                                              │  • Voice Branch │
                                              │  (RawNet + GPT) │
                                              └─────────────────┘
```

### Detection Pipeline

1. **Input Processing**: URL, screenshot, or voice file
2. **PhishSense Multimodal Analysis**:
   - **Image Branch**: Logo detection → Brand matching → CRP classification
   - **Text Branch**: HTML analysis → Suspicious pattern detection
   - **Voice Branch**: AI synthesis detection → Content analysis
3. **Feature Fusion**: Advanced decision-making algorithm combining all three modalities
4. **Result Output**: Phishing/Benign classification with confidence scores

## Technology Stack

### Frontend Technologies
- **React 18.3.1**: Modern UI framework for chat interface
- **Redux 7.2.6**: State management for application state
- **Ant Design 4.16.13**: UI component library
- **Socket.io-client 4.3.2**: Real-time WebSocket communication
- **Axios 0.24.0**: HTTP client for API requests
- **React Router DOM 5.3.0**: Client-side routing
- **js-audio-recorder 1.0.7**: Voice recording capabilities

### Backend Technologies
- **Golang 1.23**: High-performance backend server
- **Gin Framework**: HTTP web framework
- **GORM**: Object-relational mapping for database operations
- **Gorilla WebSocket**: Real-time WebSocket support
- **Kafka (IBM Sarama)**: Message queuing for real-time features
- **MySQL 8.0**: Database for user data and chat history

### AI/ML Technologies (PhishSense Core)
- **PyTorch**: Deep learning framework for detection models
- **RawNet**: Voice synthesis detection model (Voice Branch)
- **Siamese Networks**: Logo/brand matching (Image Branch)
- **CRP Classifier**: Credential page detection (Image Branch)
- **GPT-4**: Dynamic content analysis and brand recognition (All Branches)
- **OpenAI Whisper**: Voice transcription (Voice Branch)

### Infrastructure
- **Docker**: Containerized deployment
- **Docker Compose**: Multi-service orchestration
- **Nginx**: Reverse proxy and load balancing
- **WSL**: Windows Subsystem for Linux support

## Installation

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/yourusername/ChromeEx_Phish_Detector.git
cd ChromeEx_Phish_Detector

# Start all services
docker-compose -f docker-compose-integrated.yml up --build
```

### Manual Installation

#### 1. Backend Services

```bash
# Start Python phishing detection service
python start_backend.py

# Start Golang chat backend
cd Realtime-chat-app-golang
go run cmd/main.go
```

#### 2. Frontend

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
3. **Look for security icons** (🛡️) next to messages with links
4. **Click the icon** to scan for phishing
5. **Review results** with detailed analysis breakdown

### Voice Analysis

1. **Record or upload** voice messages in the chat
2. **Automatic detection** of AI-generated voices
3. **Content analysis** for phishing indicators
4. **Combined scoring** for final decision

### Additional Implementation

I have also created a Chrome extension that integrates the PhishSense model for real-time website scanning, providing browser-based phishing protection using the image and text analysis capabilities.

## API Endpoints

### Phishing Detection
- `POST /scan` - Scan website for phishing
- `POST /scan_voice` - Analyze voice file for phishing
- `GET /health` - Service health check

### Chat Backend
- `POST /user/register` - User registration
- `POST /user/login` - User authentication
- `GET /message` - Get chat messages
- `WebSocket /socket.io` - Real-time messaging

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

## Key Technologies Used

### AI/ML Libraries
- **PyTorch**: Deep learning framework
- **OpenCV**: Computer vision processing
- **Transformers**: GPT-4 integration
- **Whisper**: Speech recognition

### Web Technologies
- **React**: Frontend framework
- **Gin**: Go web framework
- **WebSocket**: Real-time communication
- **REST API**: Service communication

### Database & Messaging
- **MySQL**: Relational database
- **Kafka**: Message queuing
- **GORM**: ORM for Go

### DevOps & Deployment
- **Docker**: Containerization
- **Nginx**: Reverse proxy
- **Docker Compose**: Orchestration

## Contributing

We welcome contributions! Please see our contributing guidelines for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or issues:
- **Technical Issues**: Open an issue on GitHub
- **Research Questions**: Contact the original PhishIntention authors
- **Voice Detection**: Contact the Synthetic Voice Detection team

## Acknowledgments

- **PhishIntention Team**: For the foundational phishing detection framework
- **Synthetic Voice Detection Team**: For voice synthesis detection technology
- **Chat Application Developers**: For the real-time chat infrastructure
- **OpenAI**: For GPT-4 and Whisper integration
