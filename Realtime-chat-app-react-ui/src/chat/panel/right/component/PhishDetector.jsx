import React from 'react';
import {
  Button,
  Modal,
  message,
  Tooltip,
  Spin,
  Tag,
  Typography,
  Divider
} from 'antd';
import {
  SafetyOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { axiosPostBody } from '../../../util/Request';
import * as Params from '../../../common/param/Params';

const { Text, Title } = Typography;

class PhishDetector extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      visible: false,
      scanning: false,
      scanResult: null,
      url: ''
    };
  }

  // Extract URLs from message content
  extractURLs = (content) => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const urls = content.match(urlRegex);
    return urls || [];
  };

  // Check if message contains URLs
  hasURLs = (content) => {
    const urls = this.extractURLs(content);
    return urls.length > 0;
  };

  // Show scan modal - exposed via ref
  showScanModal = (url) => {
    this.setState({
      visible: true,
      url: url,
      scanResult: null
    });
  };

  // Handle scan button click
  handleScan = async () => {
    const { url } = this.state;

    this.setState({ scanning: true });

    try {
      const response = await axiosPostBody(Params.HOST + '/phish/scan', { url });

      if (response.data.code === 200) {
        this.setState({
          scanResult: response.data.data,
          scanning: false
        });
      } else {
        message.error('Failed to scan URL');
        this.setState({ scanning: false });
      }
    } catch (error) {
      console.error('Scan error:', error);
      message.error('Failed to connect to scanning service');
      this.setState({ scanning: false });
    }
  };

  // Close modal
  handleClose = () => {
    this.setState({
      visible: false,
      scanning: false,
      scanResult: null,
      url: ''
    });
  };

  // Render scan icon for messages with URLs
  renderScanIcon = (content) => {
    if (!this.hasURLs(content)) {
      return null;
    }

    const urls = this.extractURLs(content);
    const firstUrl = urls[0];

    return (
      <Tooltip title="Scan for phishing">
        <Button
          type="text"
          size="small"
          icon={<SafetyOutlined />}
          onClick={() => this.showScanModal(firstUrl)}
          style={{
            marginLeft: 8,
            color: '#1890ff',
            padding: '2px 4px'
          }}
        />
      </Tooltip>
    );
  };

  // Render scan result
  renderScanResult = () => {
    const { scanResult } = this.state;

    if (!scanResult) return null;

    const isPhishing = scanResult.is_phishing;
    const confidence = (scanResult.confidence * 100).toFixed(1);

    return (
      <div style={{ marginTop: 16 }}>
        <Divider />

        <div style={{ textAlign: 'center', marginBottom: 16 }}>
          {isPhishing ? (
            <div>
              <WarningOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />
              <Title level={4} style={{ color: '#ff4d4f', marginTop: 8 }}>
                WARNING: This appears to be a phishing site!
              </Title>
            </div>
          ) : (
            <div>
              <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
              <Title level={4} style={{ color: '#52c41a', marginTop: 8 }}>
                This site appears to be safe
              </Title>
            </div>
          )}

          <Tag color={isPhishing ? 'red' : 'green'} style={{ fontSize: 14 }}>
            Confidence: {confidence}%
          </Tag>
        </div>

        {scanResult.details && (
          <div>
            <Title level={5}>Analysis Details:</Title>

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
  };

  render() {
    const { visible, scanning, scanResult, url } = this.state;

    return (
      <>
        <Modal
          title={
            <div>
              <SafetyOutlined style={{ marginRight: 8 }} />
              Phishing Detection
            </div>
          }
          visible={visible}
          onCancel={this.handleClose}
          footer={[
            <Button key="close" onClick={this.handleClose}>
              Close
            </Button>,
            !scanResult && (
              <Button
                key="scan"
                type="primary"
                loading={scanning}
                onClick={this.handleScan}
                icon={<SafetyOutlined />}
              >
                {scanning ? 'Scanning...' : 'Scan Website'}
              </Button>
            )
          ]}
          width={500}
        >
          <div>
            <Text strong>URL to scan:</Text>
            <div style={{
              marginTop: 8,
              padding: 8,
              backgroundColor: '#f5f5f5',
              borderRadius: 4,
              wordBreak: 'break-all'
            }}>
              {url}
            </div>

            {scanning && (
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <Spin indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} />
                <div style={{ marginTop: 8 }}>
                  <Text>Analyzing website for phishing indicators...</Text>
                </div>
              </div>
            )}

            {this.renderScanResult()}
          </div>
        </Modal>
      </>
    );
  }
}

export default PhishDetector; 