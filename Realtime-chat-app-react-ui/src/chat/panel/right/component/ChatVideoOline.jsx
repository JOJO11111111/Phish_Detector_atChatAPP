import React from 'react';
import {
    Tooltip,
    Button,
    Drawer,
    Modal
} from 'antd';

import {
    VideoCameraOutlined,
    PoweroffOutlined
} from '@ant-design/icons';

import * as Constant from '../../../common/constant/Constant'
import { connect } from 'react-redux'
import { actions } from '../../../redux/module/panel'

let localPeer = null;
class ChatVideoOline extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            mediaPanelDrawerVisible: false,
            videoCallModal: false,
        }
    }

    componentDidMount() {
        // const configuration = {
        //     iceServers: [{
        //         "url": "stun:23.21.150.121"
        //     }, {
        //         "url": "stun:stun.l.google.com:19302"
        //     }]
        // };
        localPeer = new RTCPeerConnection();
        let peer = {
            ...this.props.peer,
            localPeer: localPeer
        }
        this.props.setPeer(peer);
        this.webrtcConnection();
    }
    videoIntervalObj = null;
    /**
     * Turn on the video phone
     */
    startVideoOnline = () => {
        if (!this.props.checkMediaPermisssion()) {
            return;
        }
        let media = {
            ...this.props.media,
            mediaConnected: false,
        }
        this.props.setMedia(media);
        this.setState({
            videoCallModal: true,
        })

        let data = {
            contentType: Constant.DIAL_VIDEO_ONLINE,
            type: Constant.MESSAGE_TRANS_TYPE,
        }
        this.props.sendMessage(data);
        this.videoIntervalObj = setInterval(() => {
            console.log("video call")
            // The other party accepts the video
            if (this.props.media && this.props.media.mediaConnected) {
                this.setMediaState();
                this.sendVideoData();
                return;
            }

            // The other party refuses to connect
            if (this.props.media && this.props.media.mediaReject) {
                this.setMediaState();
                return;
            }
            this.props.sendMessage(data);
        }, 3000)
    }

    setMediaState = () => {
        this.videoIntervalObj && clearInterval(this.videoIntervalObj);
        this.setState({
            videoCallModal: false,
        })
        let media = {
            ...this.props.media,
            mediaConnected: false,
            mediaReject: false,
        }
        this.props.setMedia(media)
    }

    sendVideoData = () => {
        let preview = document.getElementById("localPreviewSender");

        navigator.mediaDevices
            .getUserMedia({
                audio: true,
                video: true,
            }).then((stream) => {
                preview.srcObject = stream;
                stream.getTracks().forEach(track => {
                    localPeer.addTrack(track, stream);
                });

                // Be sure to pay attention: You need to put this action, here, that is, after being successful, then offer creation.Otherwise, you cannot get a flow, so you cannot play videos.
                localPeer.createOffer()
                    .then(offer => {
                        localPeer.setLocalDescription(offer);
                        let data = {
                            contentType: Constant.VIDEO_ONLINE,
                            content: JSON.stringify(offer),
                            type: Constant.MESSAGE_TRANS_TYPE,
                        }
                        this.props.sendMessage(data);
                    });
            });

        this.setState({
            mediaPanelDrawerVisible: true
        })
    }

    /**
    *webrtc binding event
    */
    webrtcConnection = () => {

        /**
         * After receiving the ICE information, the peering party is transferred to the ICE proxy of the receiving candidate information to the browser by calling the adDICANDIDATE.
         * @param {候选人信息} e 
         */
        localPeer.onicecandidate = (e) => {
            if (e.candidate) {
                // The RTCTYPE parameter defaults to the end value as ANSWER. If it is an initiative, the value will be set to offer
                let candidate = {
                    type: 'offer_ice',
                    iceCandidate: e.candidate
                }
                let message = {
                    content: JSON.stringify(candidate),
                    type: Constant.MESSAGE_TRANS_TYPE,
                }
                this.props.sendMessage(message);
            }

        };

        /**
         * After the connection is successful, get the voice and video stream from it
         * @param {包含语音视频流} e 
         */
        localPeer.ontrack = (e) => {
            if (e && e.streams) {
                let remoteVideo = document.getElementById("remoteVideoSender");
                remoteVideo.srcObject = e.streams[0];
            }
        };
    }

    /**
     * Stop video call, screen sharing
     */
    stopVideoOnline = () => {
        let preview = document.getElementById("localPreviewSender");
        if (preview && preview.srcObject && preview.srcObject.getTracks()) {
            preview.srcObject.getTracks().forEach((track) => track.stop());
        }

        let remoteVideo = document.getElementById("remoteVideoSender");
        if (remoteVideo && remoteVideo.srcObject && remoteVideo.srcObject.getTracks()) {
            remoteVideo.srcObject.getTracks().forEach((track) => track.stop());
        }
    }

    mediaPanelDrawerOnClose = () => {
        this.setState({
            mediaPanelDrawerVisible: false
        })
    }

    handleOk = () => {

    }

    handleCancel = () => {
        this.setState({
            videoCallModal: false,
        })
        let data = {
            contentType: Constant.CANCELL_VIDEO_ONLINE,
            type: Constant.MESSAGE_TRANS_TYPE,
        }
        this.props.sendMessage(data);
        this.videoIntervalObj && clearInterval(this.videoIntervalObj);
    }

    render() {
        const { chooseUser } = this.props;
        return (
            <>
                <Tooltip title="video chat">
                    <Button
                        shape="circle"
                        onClick={this.startVideoOnline}
                        style={{ marginRight: 10 }}
                        icon={<VideoCameraOutlined />} disabled={chooseUser.toUser === ''}
                    />
                </Tooltip>

                <Drawer width='820px'
                    forceRender={true}
                    title="Media panel"
                    placement="right"
                    onClose={this.mediaPanelDrawerOnClose}
                    visible={this.state.mediaPanelDrawerVisible}
                >
                    <Tooltip title="End video voice">
                        <Button
                            shape="circle"
                            onClick={this.stopVideoOnline}
                            style={{ marginRight: 10, float: 'right' }}
                            icon={<PoweroffOutlined style={{ color: 'red' }} />}
                        />
                    </Tooltip>
                    <br />
                    <video id="localPreviewSender" width="700px" height="auto" autoPlay muted controls />
                    <video id="remoteVideoSender" width="700px" height="auto" autoPlay muted controls />
                </Drawer>

                <Modal
                    title="video call"
                    visible={this.state.videoCallModal}
                    onOk={this.handleOk}
                    onCancel={this.handleCancel}
                    okText="confirm"
                    cancelText="Cancel"
                >
                    <p>Call ...</p>
                </Modal>
            </>
        );
    }
}


function mapStateToProps(state) {
    return {
        chooseUser: state.panelReducer.chooseUser,
        socket: state.panelReducer.socket,
        peer: state.panelReducer.peer,
        media: state.panelReducer.media,
    }
}

function mapDispatchToProps(dispatch) {
    return {
        setMedia: (data) => dispatch(actions.setMedia(data)),
        setPeer: (data) => dispatch(actions.setPeer(data)),
    }
}

ChatVideoOline = connect(mapStateToProps, mapDispatchToProps)(ChatVideoOline)

export default ChatVideoOline