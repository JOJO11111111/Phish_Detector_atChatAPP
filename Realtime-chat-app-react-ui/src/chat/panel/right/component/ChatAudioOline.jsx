import React from 'react';
import {
    Tooltip,
    Button,
    Drawer
} from 'antd';

import {
    PhoneOutlined,
    PoweroffOutlined
} from '@ant-design/icons';

import * as Constant from '../../../common/constant/Constant'
import { connect } from 'react-redux'
import { actions } from '../../../redux/module/panel'

let localPeer = null;
class ChatAudioOline extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            mediaPanelDrawerVisible: false,
        }
    }

    componentDidMount() {
        localPeer = new RTCPeerConnection();
        let peer = {
            ...this.props.peer,
            localPeer: localPeer
        }
        this.props.setPeer(peer);
    }
    /**
     * Turn on the voice call
     */
    startAudioOnline = () => {
        if (!this.props.checkMediaPermisssion()) {
            return;
        }

        this.webrtcConnection();
        navigator.mediaDevices
            .getUserMedia({
                audio: true,
                video: false,
            }).then((stream) => {
                stream.getTracks().forEach(track => {
                    localPeer.addTrack(track, stream);
                });

                // Be sure to pay attention: You need to put this action, here, that is, after being successful, then offer creation.Otherwise, you cannot get a flow, so you cannot play videos.
                localPeer.createOffer()
                    .then(offer => {
                        localPeer.setLocalDescription(offer);
                        let data = {
                            contentType: Constant.AUDIO_ONLINE,  // Message content type
                            content: JSON.stringify(offer),
                            type: Constant.MESSAGE_TRANS_TYPE,   // Message transmission type
                        }
                        this.props.sendMessage(data);
                    });
            });

        this.setState({
            mediaPanelDrawerVisible: true
        })
    }

    /**
    * webrtc binding event
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
                let remoteAudio = document.getElementById("remoteAudioPhone");
                remoteAudio.srcObject = e.streams[0];
            }
        };
    }

    /**
     * Stop voice call
     */
    stopAudioOnline = () => {
        let audioPhone = document.getElementById("remoteAudioPhone");
        if (audioPhone && audioPhone.srcObject && audioPhone.srcObject.getTracks()) {
            audioPhone.srcObject.getTracks().forEach((track) => track.stop());
        }
    }

    mediaPanelDrawerOnClose = () => {
        this.setState({
            mediaPanelDrawerVisible: false
        })
    }

    render() {
        const { chooseUser } = this.props;
        return (
            <>
                <Tooltip title="Voice chat">
                    <Button
                        shape="circle"
                        onClick={this.startAudioOnline}
                        style={{ marginRight: 10 }}
                        icon={<PhoneOutlined />}
                        disabled={chooseUser.toUser === ''}
                    />
                </Tooltip>

                <Drawer width='420px'
                    forceRender={true}
                    title="Media panel"
                    placement="right"
                    onClose={this.mediaPanelDrawerOnClose}
                    visible={this.state.mediaPanelDrawerVisible}
                >
                    <Tooltip title="End video voice">
                        <Button
                            shape="circle"
                            onClick={this.stopAudioOnline}
                            style={{ marginRight: 10, float: 'right' }}
                            icon={<PoweroffOutlined style={{ color: 'red' }} />}
                        />
                    </Tooltip>
                    <br />

                    <audio id="remoteAudioPhone" autoPlay controls />
                </Drawer>
            </>
        );
    }
}


function mapStateToProps(state) {
    return {
        chooseUser: state.panelReducer.chooseUser,
        socket: state.panelReducer.socket,
        peer: state.panelReducer.peer,
    }
}

function mapDispatchToProps(dispatch) {
    return {
        setMedia: (data) => dispatch(actions.setMedia(data)),
        setPeer: (data) => dispatch(actions.setPeer(data)),
    }
}

ChatAudioOline = connect(mapStateToProps, mapDispatchToProps)(ChatAudioOline)

export default ChatAudioOline