import React from 'react';
import { Comment, Button, Tooltip, Modal, message, Input, Radio, Space, Tag, Typography, Alert, Divider, Row, Col, Statistic } from 'antd';
import { SafetyOutlined, LinkOutlined, WarningOutlined, CheckCircleOutlined, AudioOutlined } from '@ant-design/icons';

const { TextArea } = Input;
const { Text } = Typography;

class SafeComment extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      modalVisible: false,
      scanning: false,
      urlToScan: '',
      scanMode: 'auto', // 'auto' or 'manual'
      scanResult: null,
      resultsModalVisible: false,
      detectionType: 'url' // 'url' or 'voice'
    };
  }

  // Extract URLs from message content
  extractURLs = (content) => {
    console.log('Extracting URLs from content:', content);
    console.log('Content type:', typeof content);

    if (typeof content === 'string') {
      // More comprehensive URL regex
      const urlRegex = /(https?:\/\/[^\s<>"{}|\\^`\[\]]+)/gi;
      const urls = content.match(urlRegex);
      console.log('Extracted URLs:', urls);
      return urls || [];
    }

    // If content is a React element, try to extract text
    if (React.isValidElement(content)) {
      console.log('Content is React element, extracting text...');
      // Try to get text content from React element
      const textContent = this.extractTextFromReactElement(content);
      console.log('Extracted text from React element:', textContent);
      const urlRegex = /(https?:\/\/[^\s<>"{}|\\^`\[\]]+)/gi;
      const urls = textContent.match(urlRegex);
      console.log('Extracted URLs from React element:', urls);
      return urls || [];
    }

    console.log('No URLs found');
    return [];
  };

  // Extract text from React element
  extractTextFromReactElement = (element) => {
    if (typeof element === 'string') {
      return element;
    }

    if (React.isValidElement(element)) {
      // If it has children, recursively extract text
      if (element.props && element.props.children) {
        if (Array.isArray(element.props.children)) {
          return element.props.children.map(child => this.extractTextFromReactElement(child)).join(' ');
        } else {
          return this.extractTextFromReactElement(element.props.children);
        }
      }

      // If it has a text content property
      if (element.props && element.props.content) {
        return element.props.content;
      }
    }

    return '';
  };

  // Check if message contains URLs
  hasURLs = (content) => {
    const urls = this.extractURLs(content);
    return urls.length > 0;
  };

  // Check if message is voice/audio
  isVoiceMessage = (contentType) => {
    // Voice messages have contentType = 4
    return contentType === 4;
  };

  // Show scan modal
  showScanModal = () => {
    const { content, contentType, url } = this.props;
    const urls = this.extractURLs(content);
    const isVoice = this.isVoiceMessage(contentType);

    console.log('showScanModal - props:', this.props);
    console.log('showScanModal - contentType:', contentType);
    console.log('showScanModal - url:', url);
    console.log('showScanModal - isVoice:', isVoice);

    let detectionType = 'url';
    let scanMode = 'auto';
    let urlToScan = '';

    if (isVoice) {
      detectionType = 'voice';
    } else if (urls.length > 0) {
      detectionType = 'url';
      urlToScan = urls[0]; // Auto-fill with first URL
      scanMode = 'auto';
    } else {
      detectionType = 'url';
      scanMode = 'manual';
    }

    console.log('showScanModal - detectionType:', detectionType);

    this.setState({
      modalVisible: true,
      detectionType,
      scanMode,
      urlToScan
    });
  };

  // Handle scan button click
  handleScan = async () => {
    const { detectionType, urlToScan, scanMode } = this.state;

    let finalUrl = urlToScan;

    // If auto-detect mode, extract URL from message content
    if (detectionType === 'url' && scanMode === 'auto') {
      const { content } = this.props;
      const urls = this.extractURLs(content);
      if (urls.length > 0) {
        finalUrl = urls[0];
      } else {
        message.error('No URL found in message content');
        return;
      }
    }

    if (detectionType === 'url' && !finalUrl.trim()) {
      message.error('Please enter a URL to scan');
      return;
    }

    this.setState({ scanning: true });

    try {
      if (detectionType === 'url') {
        // Call the Python Flask phishing detection service directly
        const response = await fetch('http://localhost:5000/scan', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            url: finalUrl.trim()
          })
        });

        if (!response.ok) {
          throw new Error(`Server responded with status: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
          message.error('Error: ' + data.error);
          this.setState({ scanning: false });
          return;
        }

        // Display results in a new modal
        this.setState({
          scanning: false,
          modalVisible: false,
          scanResult: data,
          resultsModalVisible: true
        });

      } else if (detectionType === 'voice') {
        // Call the Python Flask voice detection service
        const { url } = this.props;

        const response = await fetch('http://localhost:5000/scan_voice', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            voice_filename: url
          })
        });

        if (!response.ok) {
          throw new Error(`Server responded with status: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
          message.error('Error: ' + data.error);
          this.setState({ scanning: false });
          return;
        }

        // Display results in a new modal
        this.setState({
          scanning: false,
          modalVisible: false,
          scanResult: data,
          resultsModalVisible: true
        });
      }
    } catch (error) {
      console.error('Scan error:', error);
      message.error('Failed to connect to detection service. Make sure the backend is running.');
      this.setState({ scanning: false });
    }
  };

  // Close modal
  handleClose = () => {
    this.setState({
      modalVisible: false,
      scanning: false,
      urlToScan: '',
      scanMode: 'auto',
      detectionType: 'url'
    });
  };

  // Close results modal
  handleResultsClose = () => {
    this.setState({
      resultsModalVisible: false,
      scanResult: null
    });
  };

  // Handle URL input change
  handleUrlChange = (e) => {
    this.setState({ urlToScan: e.target.value });
  };

  // Handle scan mode change
  handleScanModeChange = (e) => {
    this.setState({ scanMode: e.target.value });
  };

  // Render content with security icon for every message
  renderContent = (content) => {
    return (
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ flex: 1 }}>
          {content}
        </div>
        <div style={{ marginLeft: 8, marginTop: 4 }}>
          <Tooltip title="Detect phishing content">
            <Button
              type="text"
              size="small"
              icon={<SafetyOutlined />}
              onClick={this.showScanModal}
              style={{
                color: '#1890ff',
                padding: '2px 4px'
              }}
            />
          </Tooltip>
        </div>
      </div>
    );
  };

  // Render URL detection content
  renderUrlDetection = () => {
    const { urlToScan, scanMode } = this.state;
    const { content } = this.props;
    const urls = this.extractURLs(content);

    console.log('renderUrlDetection - content:', content);
    console.log('renderUrlDetection - urls:', urls);
    console.log('renderUrlDetection - scanMode:', scanMode);

    return (
      <div>
        <p>Would you like to detect if this message contains phishing content?</p>

        <div style={{ marginBottom: 16 }}>
          <Radio.Group value={scanMode} onChange={this.handleScanModeChange}>
            <Space direction="vertical">
              <Radio value="auto">Auto-detect URLs in message</Radio>
              <Radio value="manual">Manually enter URL to check</Radio>
            </Space>
          </Radio.Group>
        </div>

        {scanMode === 'manual' && (
          <div style={{ marginBottom: 16 }}>
            <p><strong>Paste the URL you want to check:</strong></p>
            <TextArea
              value={urlToScan}
              onChange={this.handleUrlChange}
              placeholder="https://example.com"
              rows={2}
              style={{ marginTop: 8 }}
            />
          </div>
        )}

        {scanMode === 'auto' && urls.length > 0 && (
          <div style={{
            marginTop: 8,
            padding: 8,
            backgroundColor: '#f5f5f5',
            borderRadius: 4,
            wordBreak: 'break-all'
          }}>
            <p><strong>Detected URL:</strong></p>
            <p>{urls[0]}</p>
          </div>
        )}

        {scanMode === 'auto' && urls.length === 0 && (
          <div style={{
            marginTop: 8,
            padding: 8,
            backgroundColor: '#fff2e8',
            borderRadius: 4,
            border: '1px solid #ffbb96'
          }}>
            <p><strong>⚠️ No URLs detected in message</strong></p>
            <p>Switch to manual mode to enter a URL, or check if the message contains a valid URL.</p>
            <p><strong>Debug info:</strong></p>
            <p>Content type: {typeof content}</p>
            <p>Content: {JSON.stringify(content)}</p>
          </div>
        )}

        <div style={{
          marginTop: 8,
          padding: 8,
          backgroundColor: '#f0f8ff',
          borderRadius: 4,
          border: '1px solid #d6e4ff'
        }}>
          <p><strong>Message content:</strong></p>
          <p>{typeof content === 'string' ? content : 'Message content'}</p>
        </div>
      </div>
    );
  };

  // Render voice detection content
  renderVoiceDetection = () => {
    const { url, contentType } = this.props;

    // Construct the full file path
    const fullFilePath = `./Realtime-chat-app-golang/web/static/file/${url}`;

    return (
      <div>
        <div style={{ textAlign: 'center', marginBottom: 16 }}>
          <AudioOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          <h3>Voice Message Detection</h3>
        </div>

        <p>This is a voice message. Do you want to check if it's AI generated?</p>

        <div style={{
          marginTop: 16,
          padding: 12,
          backgroundColor: '#fff7e6',
          borderRadius: 4,
          border: '1px solid #ffd591'
        }}>
          <p><strong>Voice Analysis Features:</strong></p>
          <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
            <li>Detect AI-generated voice patterns</li>
            <li>Identify synthetic speech characteristics</li>
            <li>Analyze voice consistency and naturalness</li>
            <li>Check for common AI voice artifacts</li>
          </ul>
        </div>

        {/* File Path Information */}
        <div style={{
          marginTop: 16,
          padding: 12,
          backgroundColor: '#f0f8ff',
          borderRadius: 4,
          border: '1px solid #d6e4ff'
        }}>
          <p><strong>Voice File Information:</strong></p>
          <p><strong>Content Type:</strong> {contentType} (Voice Message)</p>
          <p><strong>File Name:</strong> {url}</p>
          <p><strong>Full File Path:</strong></p>
          <div style={{
            padding: 8,
            backgroundColor: '#f5f5f5',
            borderRadius: 4,
            fontFamily: 'monospace',
            fontSize: '12px',
            wordBreak: 'break-all'
          }}>
            {fullFilePath}
          </div>
        </div>
      </div>
    );
  };

  // Render scan results
  renderScanResults = () => {
    const { scanResult, detectionType } = this.state;

    if (!scanResult) return null;

    const isPhishing = scanResult.is_phishing;
    const isVoiceDetection = detectionType === 'voice';

    if (isVoiceDetection) {
      // Voice detection logic
      const voicePhishScore = scanResult.details?.voice_phish_score || 0;
      const voiceVector = scanResult.details?.voice_vector || '';
      const voiceFeatures = voiceVector.split('|').map(Number);

      // Parse voice features: [ai_score, ai_weight, ask_money, ask_pw, ask_info, other_sus]
      const aiScore = voiceFeatures[0] || 0;
      const aiWeight = voiceFeatures[1] || 0;
      const askMoney = voiceFeatures[2] || 0;
      const askPassword = voiceFeatures[3] || 0;
      const askInfo = voiceFeatures[4] || 0;
      const otherSuspicious = voiceFeatures[5] || 0;

      // Use the boosted AI score from backend if available, otherwise use original
      const displayAIScore = scanResult.details?.ai_score_boosted || aiScore;

      // Normalize the voice phish score to 0-1 range (original fusion can be high)
      const normalizedVoicePhishScore = Math.min(voicePhishScore / 10.0, 1.0);
      const isHighVishingRisk = normalizedVoicePhishScore > 0.3; // 30% threshold
      const isAIGenerated = displayAIScore > 0.08; // 8% AI threshold
      const hasSuspiciousContent = askMoney > 0 || askPassword > 0 || askInfo > 0 || otherSuspicious > 0;
      const isAIImpersonation = isAIGenerated && hasSuspiciousContent;

      return (
        <div style={{ marginTop: 16 }}>
          <div style={{ textAlign: 'center', marginBottom: 16 }}>
            {isHighVishingRisk ? (
              <div>
                <WarningOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
                <h3 style={{ color: '#ff4d4f', marginTop: 8 }}>
                  ⚠️ HIGH VISHING RISK DETECTED!
                </h3>
              </div>
            ) : (
              <div>
                <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
                <h3 style={{ color: '#52c41a', marginTop: 8 }}>
                  Voice appears to be authentic
                </h3>
              </div>
            )}
          </div>

          {scanResult.details && (
            <div>
              {scanResult.details.transcript && (
                <div style={{ marginBottom: 20 }}>
                  <h4>📝 Transcribed Message:</h4>
                  <div style={{
                    padding: 16,
                    backgroundColor: '#f8f9fa',
                    borderRadius: 8,
                    border: '2px solid #e9ecef',
                    marginTop: 8,
                    maxHeight: '150px',
                    overflowY: 'auto'
                  }}>
                    <Text style={{
                      fontSize: '14px',
                      lineHeight: '1.5',
                      color: '#495057',
                      fontFamily: 'inherit'
                    }}>
                      "{scanResult.details.transcript}"
                    </Text>
                  </div>
                </div>
              )}

              <h4>Voice Analysis Details:</h4>

              <div style={{ marginBottom: 12 }}>
                <Text strong>Voice Phish Score: </Text>
                <Text style={{ color: isHighVishingRisk ? '#ff4d4f' : '#52c41a', fontWeight: 'bold' }}>
                  {(normalizedVoicePhishScore * 100).toFixed(1)}%
                </Text>
                {isHighVishingRisk && (
                  <Text style={{ color: '#ff4d4f', marginLeft: 8 }}>
                    (Above 30% threshold - High vishing risk)
                  </Text>
                )}
              </div>

              <div style={{ marginBottom: 12 }}>
                <Text strong>AI Generation Detection:</Text>
                <div style={{ marginLeft: 16 }}>
                  <Text>AI Score: {(displayAIScore * 100).toFixed(1)}%</Text><br />
                  <Text style={{ color: isAIGenerated ? '#ff4d4f' : '#52c41a' }}>
                    Status: {isAIGenerated ? 'LIKELY AI-GENERATED' : 'Likely Authentic'}
                  </Text>
                </div>
              </div>

              <div style={{ marginBottom: 12 }}>
                <Text strong>Content Analysis:</Text>
                <div style={{ marginLeft: 16 }}>
                  <Text>Asking for Money: {(askMoney * 10).toFixed(1)}%</Text><br />
                  <Text>Asking for Password: {(askPassword * 10).toFixed(1)}%</Text><br />
                  <Text>Asking for Personal Info: {(askInfo * 10).toFixed(1)}%</Text><br />
                  <Text>Other Suspicious Content: {(otherSuspicious * 10).toFixed(1)}%</Text>
                </div>
              </div>

              {isAIImpersonation && (
                <div style={{
                  marginTop: 16,
                  padding: 16,
                  backgroundColor: '#fff2f0',
                  borderRadius: 8,
                  border: '2px solid #ff4d4f'
                }}>
                  <h4 style={{ color: '#ff4d4f', marginBottom: 12 }}>
                    🚨 CRITICAL WARNING: AI-GENERATED VOICE DETECTED
                  </h4>
                  <p style={{ marginBottom: 8 }}>
                    <strong>This voice appears to be AI-generated and contains suspicious content.</strong>
                  </p>
                  <p style={{ marginBottom: 8 }}>
                    <strong>⚠️ Are you sure this is the real person you're talking to?</strong>
                  </p>
                  <p style={{ marginBottom: 8 }}>
                    This could be an AI impersonating your friend or family member's voice.
                    <strong>Do not provide any personal information, passwords, or money.</strong>
                  </p>
                  <p style={{ color: '#ff4d4f', fontWeight: 'bold' }}>
                    🛡️ RECOMMENDATION: Contact the person through a different method to verify their identity.
                  </p>
                </div>
              )}

              {isHighVishingRisk && !isAIImpersonation && (
                <div style={{
                  marginTop: 16,
                  padding: 16,
                  backgroundColor: '#fff7e6',
                  borderRadius: 8,
                  border: '2px solid #faad14'
                }}>
                  <h4 style={{ color: '#faad14', marginBottom: 12 }}>
                    ⚠️ VISHING WARNING
                  </h4>
                  <p style={{ marginBottom: 8 }}>
                    <strong>This voice message shows signs of vishing (voice phishing).</strong>
                  </p>
                  <p style={{ marginBottom: 8 }}>
                    Be cautious about any requests for personal information, passwords, or money.
                  </p>
                  <p style={{ color: '#faad14', fontWeight: 'bold' }}>
                    🛡️ RECOMMENDATION: Verify the request through other means before responding.
                  </p>
                </div>
              )}

              <div style={{ marginBottom: 12 }}>
                <Text strong>File Information:</Text>
                <div style={{ marginLeft: 16 }}>
                  <Text>File Name: {scanResult.details.voice_filename}</Text>
                </div>
              </div>

              {scanResult.details.transcript && (
                <div style={{ marginBottom: 12 }}>
                  <Text strong>Transcribed Message:</Text>
                  <div style={{
                    marginLeft: 16,
                    marginTop: 8,
                    padding: 12,
                    backgroundColor: '#f0f8ff',
                    borderRadius: 8,
                    border: '1px solid #d9d9d9',
                    maxHeight: '200px',
                    overflowY: 'auto'
                  }}>
                    <Text style={{ fontStyle: 'italic', color: '#666' }}>
                      "{scanResult.details.transcript}"
                    </Text>
                  </div>
                </div>
              )}

              {scanResult.details.voice_vector && (
                <div style={{ marginBottom: 12 }}>
                  <Text strong>Voice Features (AI|Weight|Money|Password|Info|Other):</Text>
                  <div style={{
                    marginLeft: 16,
                    padding: 8,
                    backgroundColor: '#f5f5f5',
                    borderRadius: 4,
                    fontFamily: 'monospace',
                    fontSize: '12px'
                  }}>
                    {scanResult.details.voice_vector}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      );
    } else {
      // URL detection results (unchanged)
      const confidence = (scanResult.confidence * 100).toFixed(1);

      return (
        <div style={{ marginTop: 16 }}>
          <div style={{ textAlign: 'center', marginBottom: 16 }}>
            {isPhishing ? (
              <div>
                <WarningOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
                <h3 style={{ color: '#ff4d4f', marginTop: 8 }}>
                  WARNING: This appears to be a phishing site!
                </h3>
              </div>
            ) : (
              <div>
                <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
                <h3 style={{ color: '#52c41a', marginTop: 8 }}>
                  This site appears to be safe
                </h3>
              </div>
            )}

            <Tag color={isPhishing ? 'red' : 'green'} style={{ fontSize: 14 }}>
              Confidence: {confidence}%
            </Tag>
          </div>

          {scanResult.details && (
            <div>
              <h4>Analysis Details:</h4>

              <div style={{ marginBottom: 12 }}>
                <Text strong>Image Analysis:</Text>
                <div style={{ marginLeft: 16 }}>
                  <Text>Phish Score: {(scanResult.details.image_phish_score * 100).toFixed(1)}%</Text><br />
                  <Text>Decision: {scanResult.details.image_decision === 1 ? 'Phishing' : 'Benign'}</Text>
                </div>
              </div>

              <div>
                <Text strong>Text Analysis:</Text>
                <div style={{ marginLeft: 16 }}>
                  <Text>Phish Score: {(scanResult.details.text_phish_score * 100).toFixed(1)}%</Text><br />
                  <Text>Decision: {scanResult.details.text_decision === 1 ? 'Phishing' : 'Benign'}</Text>
                </div>
              </div>
            </div>
          )}
        </div>
      );
    }
  };

  render() {
    const { content, ...otherProps } = this.props;
    const { modalVisible, scanning, detectionType, resultsModalVisible, scanResult } = this.state;

    return (
      <>
        <Comment
          {...otherProps}
          content={this.renderContent(content)}
        />

        {/* Scan Modal */}
        <Modal
          title={
            <div>
              <SafetyOutlined style={{ marginRight: 8 }} />
              Phishing Detection
            </div>
          }
          visible={modalVisible}
          onCancel={this.handleClose}
          footer={[
            <Button key="close" onClick={this.handleClose}>
              Close
            </Button>,
            <Button
              key="scan"
              type="primary"
              loading={scanning}
              onClick={this.handleScan}
              icon={this.state.detectionType === 'url' ? <LinkOutlined /> : <AudioOutlined />}
            >
              {scanning ? 'Scanning...' :
                this.state.detectionType === 'url' ? 'Detect Phishing' : 'Analyze Voice'}
            </Button>
          ]}
          width={500}
        >
          <div>
            {this.state.detectionType === 'url' ? this.renderUrlDetection() : this.renderVoiceDetection()}

            {scanning && (
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <p>
                  {this.state.detectionType === 'url'
                    ? 'Analyzing URL for phishing indicators...'
                    : 'Analyzing voice for AI generation patterns...'}
                </p>
              </div>
            )}
          </div>
        </Modal>

        {/* Results Modal */}
        <Modal
          title="Detection Results"
          visible={resultsModalVisible}
          onCancel={() => this.setState({ resultsModalVisible: false })}
          footer={[
            <Button key="close" onClick={() => this.setState({ resultsModalVisible: false })}>
              Close
            </Button>
          ]}
          width={600}
        >
          {scanResult && this.renderScanResults()}
        </Modal>
      </>
    );
  }
}

export default SafeComment; 