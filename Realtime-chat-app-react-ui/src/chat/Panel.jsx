import React from 'react';
import {
    Button,
    Row,
    Col,
    message,
    Drawer,
    Tooltip,
    Modal
} from 'antd';
import {
    PoweroffOutlined,
    FileOutlined,
} from '@ant-design/icons';
import moment from 'moment';
import * as Params from './common/param/Params'
import * as Constant from './common/constant/Constant'
import Center from './panel/center/index'
import Left from './panel/left/index'
import Right from './panel/right/index'

import protobuf from './proto/proto'
import { connect } from 'react-redux'
import { actions } from './redux/module/panel'

var socket = null;
var peer = null;
var lockConnection = false;

var heartCheck = {
    timeout: 10000,
    timeoutObj: null,
    serverTimeoutObj: null,
    num: 3,
    start: function () {
        var self = this;
        var _num = this.num
        this.timeoutObj && clearTimeout(this.timeoutObj);
        this.serverTimeoutObj && clearTimeout(this.serverTimeoutObj);
        this.timeoutObj = setTimeout(function () {
            //Send a heartbeat here. After receiving the back end, a heartbeat message is returned.
            //Oncessage gets the return heartbeat and it means that the connection is normal
            let data = {
                type: "heatbeat",
                content: "ping",
            }

            if (socket.readyState === 1) {
                let message = protobuf.lookup("protocol.Message")
                const messagePB = message.create(data)
                socket.send(message.encode(messagePB).finish())
            }

            self.serverTimeoutObj = setTimeout(function () {
                _num--
                if (_num <= 0) {
                    console.log("the ping num is more then 3, close socket!")
                    socket.close();
                }
            }, self.timeout);

        }, this.timeout)
    }
}

class Panel extends React.Component {
    constructor(props) {
        super(props)
        localStorage.uuid = props.match.params.user;
        this.state = {
            onlineType: 1, // Online video or audio: 1 video, 2 audio
            video: {
                height: 400,
                width: 540
            },
            share: {
                height: 540,
                width: 750
            },
            currentScreen: {
                height: 0,
                width: 0
            },
            videoCallModal: false,
            callName: '',
            fromUserUuid: '',
        }
    }

    componentDidMount() {
        this.connection()
    }

    /**
     * websocket连接
     */
    connection = () => {
        console.log("to connect...")
        peer = new RTCPeerConnection();
        var image = document.getElementById('receiver');
        socket = new WebSocket("ws://" + Params.IP_PORT + "/socket.io?user=" + this.props.match.params.user)

        socket.onopen = () => {
            heartCheck.start()
            console.log("connected")
            this.webrtcConnection()

            this.props.setSocket(socket);
        }
        socket.onmessage = (message) => {
            heartCheck.start()

            // The received MESSAGE.DATA is a blob object.You need to convert this object to ArrayBuffer to perform propo analysis
            let messageProto = protobuf.lookup("protocol.Message")
            let reader = new FileReader();
            reader.readAsArrayBuffer(message.data);
            reader.onload = ((event) => {
                let messagePB = messageProto.decode(new Uint8Array(event.target.result))
                console.log(messagePB)
                if (messagePB.type === "heatbeat") {
                    return;
                }

                // Accept voice calls or video phone webrtccccccccccccccccccccccc
                if (messagePB.type === Constant.MESSAGE_TRANS_TYPE) {
                    this.dealWebRtcMessage(messagePB);
                    return;
                }

                // If the news is not chatting, show unreasonable reminder
                if (this.props.chooseUser.toUser !== messagePB.from) {
                    this.showUnreadMessageDot(messagePB.from);
                    return;
                }

                // Video image
                if (messagePB.contentType === 8) {
                    let currentScreen = {
                        width: this.state.video.width,
                        height: this.state.video.height
                    }
                    this.setState({
                        currentScreen: currentScreen
                    })
                    image.src = messagePB.content
                    return;
                }

                // Screen sharing
                if (messagePB.contentType === 9) {
                    let currentScreen = {
                        width: this.state.share.width,
                        height: this.state.share.height
                    }
                    this.setState({
                        currentScreen: currentScreen
                    })
                    image.src = messagePB.content
                    return;
                }

                // // Accept voice calls or video phone webrtccccccccccccccccccccccc
                // if (messagePB.type === Constant.MESSAGE_TRANS_TYPE) {
                //     this.dealWebRtcMessage(messagePB);
                //     return;
                // }

                let avatar = this.props.chooseUser.avatar
                if (messagePB.messageType === 2) {
                    avatar = Params.HOST + "/file/" + messagePB.avatar
                }

                // File content, recorded videos, voice content
                let content = this.getContentByType(messagePB.contentType, messagePB.url, messagePB.content)
                let messageList = [
                    ...this.props.messageList,
                    {
                        author: messagePB.fromUsername,
                        avatar: avatar,
                        content: <p>{content}</p>,
                        datetime: moment().fromNow(),
                        contentType: messagePB.contentType,
                        url: messagePB.url
                    },
                ];
                this.props.setMessageList(messageList);
            })
        }

        socket.onclose = (_message) => {
            console.log("close and reconnect-->--->")

            this.reconnect()
        }

        socket.onerror = (_message) => {
            console.log("error----->>>>")

            this.reconnect()
        }
    }

    /**
     * webrtc binding event
     */
    webrtcConnection = () => {
        /**
         * After receiving the ICE information, the peering party is transferred to the ICE proxy of the receiving candidate information to the browser by calling the adDICANDIDATE.
         * @param {Candidate information} e 
         */
        peer.onicecandidate = (e) => {
            if (e.candidate) {
                // The RTCTYPE parameter defaults to the end value ANSWER. If it is an initiative, the value will be set to OFFEr
                let candidate = {
                    type: 'answer_ice',
                    iceCandidate: e.candidate
                }
                let message = {
                    content: JSON.stringify(candidate),
                    type: Constant.MESSAGE_TRANS_TYPE,
                }
                this.sendMessage(message);
            }

        };

        /**
         * After the connection is successful, get the voice and video stream from it
         * @param {Including voice and video stream} e 
         */
        peer.ontrack = (e) => {
            if (e && e.streams) {
                if (this.state.onlineType === 1) {
                    let remoteVideo = document.getElementById("remoteVideoReceiver");
                    remoteVideo.srcObject = e.streams[0];
                } else {
                    let remoteAudio = document.getElementById("audioPhone");
                    remoteAudio.srcObject = e.streams[0];
                }
            }
        };
    }

    /**
     * Process WebRTC messages, including offer of obtaining the request party, responding to Answer, etc.
     * @param {Content}} messagePB 
     */
    dealWebRtcMessage = (messagePB) => {
        if (messagePB.contentType >= Constant.DIAL_MEDIA_START && messagePB.contentType <= Constant.DIAL_MEDIA_END) {
            this.dealMediaCall(messagePB);
            return;
        }
        const { type, sdp, iceCandidate } = JSON.parse(messagePB.content);

        if (type === "answer") {
            const answerSdp = new RTCSessionDescription({ type, sdp });
            this.props.peer.localPeer.setRemoteDescription(answerSdp)
        } else if (type === "answer_ice") {
            this.props.peer.localPeer.addIceCandidate(iceCandidate)
        } else if (type === "offer_ice") {
            peer.addIceCandidate(iceCandidate)
        } else if (type === "offer") {
            if (!this.checkMediaPermisssion()) {
                return;
            }
            let preview

            let video = false;
            if (messagePB.contentType === Constant.VIDEO_ONLINE) {
                preview = document.getElementById("localVideoReceiver");
                video = true
                this.setState({
                    onlineType: 1,
                })
            } else {
                preview = document.getElementById("audioPhone");
                this.setState({
                    onlineType: 2,
                })
            }

            navigator.mediaDevices
                .getUserMedia({
                    audio: true,
                    video: video,
                }).then((stream) => {
                    preview.srcObject = stream;
                    stream.getTracks().forEach(track => {
                        peer.addTrack(track, stream);
                    });

                    // Be sure to pay attention: need to put this action in it, that is, after being successful, and then create ANSWER creation.Otherwise, you cannot get a flow, so you cannot play videos.
                    const offerSdp = new RTCSessionDescription({ type, sdp });
                    peer.setRemoteDescription(offerSdp)
                        .then(() => {
                            peer.createAnswer().then(answer => {
                                peer.setLocalDescription(answer)

                                let message = {
                                    content: JSON.stringify(answer),
                                    type: Constant.MESSAGE_TRANS_TYPE,
                                    messageType: messagePB.contentType
                                }
                                this.sendMessage(message);
                            })
                        });
                });
        }
    }

    /**
     * Re -connect after disconnecting
     */
    reconnectTimeoutObj = null;
    reconnect = () => {
        if (lockConnection) return;
        lockConnection = true

        this.reconnectTimeoutObj && clearTimeout(this.reconnectTimeoutObj)

        this.reconnectTimeoutObj = setTimeout(() => {
            if (socket.readyState !== 1) {
                this.connection()
            }
            lockConnection = false
        }, 10000)
    }

    /**
     * Check whether the media permissions open
     * @returns Whether the media permissions open
     */
    checkMediaPermisssion = () => {
        navigator.getUserMedia = navigator.getUserMedia ||
            navigator.webkitGetUserMedia ||
            navigator.mozGetUserMedia ||
            navigator.msGetUserMedia; //Get the media object (here refers to the camera)
        if (!navigator || !navigator.mediaDevices) {
            message.error("Obtaining the permission of the camera failed！")
            return false;
        }
        return true;
    }

    /**
      * Send message
      * @param {Content} messageData 
      */
    sendMessage = (messageData) => {
        let toUser = messageData.toUser;
        if (null == toUser) {
            toUser = this.props.chooseUser.toUser;
        }
        let data = {
            ...messageData,
            messageType: this.props.chooseUser.messageType, // Message type, 1. Single chat 2. Group chat
            fromUsername: localStorage.username,
            from: localStorage.uuid,
            to: toUser,
        }
        let message = protobuf.lookup("protocol.Message")
        const messagePB = message.create(data)

        socket.send(message.encode(messagePB).finish())
    }

    /**
     *Labels corresponding to the rendering of the file type, such as videos, pictures, etc.。
     * @param {File type} type 
     * @param {File address} url 
     * @returns 
     */
    getContentByType = (type, url, content) => {
        if (type === 2) {
            content = <FileOutlined style={{ fontSize: 38 }} />
        } else if (type === 3) {
            content = <img src={Params.HOST + "/file/" + url} alt="" width="150px" />
        } else if (type === 4) {
            content = <audio src={Params.HOST + "/file/" + url} controls autoPlay={false} preload="auto" />
        } else if (type === 5) {
            content = <video src={Params.HOST + "/file/" + url} controls autoPlay={false} preload="auto" width='200px' />
        }

        return content;
    }

    /**
     * Stop video call, screen sharing
     */
    stopVideoOnline = () => {
        this.setState({
            isRecord: false
        })

        let localVideoReceiver = document.getElementById("localVideoReceiver");
        if (localVideoReceiver && localVideoReceiver.srcObject && localVideoReceiver.srcObject.getTracks()) {
            localVideoReceiver.srcObject.getTracks().forEach((track) => track.stop());
        }

        let preview = document.getElementById("preview");
        if (preview && preview.srcObject && preview.srcObject.getTracks()) {
            preview.srcObject.getTracks().forEach((track) => track.stop());
        }

        let audioPhone = document.getElementById("audioPhone");
        if (audioPhone && audioPhone.srcObject && audioPhone.srcObject.getTracks()) {
            audioPhone.srcObject.getTracks().forEach((track) => track.stop());
        }
        this.dataChunks = []

        // When you stop video or screen sharing, you will minimize the canvas
        let currentScreen = {
            width: 0,
            height: 0
        }
        this.setState({
            currentScreen: currentScreen
        })
    }

    /**
     * Display video or audio panel
     */
    mediaPanelDrawerOnClose = () => {
        let media = {
            ...this.props.media,
            showMediaPanel: false,
        }
        this.props.setMedia(media)
    }

    /**
     * If the receiving message is not the message of chat, it shows unreasonable reminder
     * @param {UUID sent to the corresponding personnel} toUuid 
     */
    showUnreadMessageDot = (toUuid) => {
        let userList = this.props.userList;
        for (var index in userList) {
            if (userList[index].uuid === toUuid) {
                userList[index].hasUnreadMessage = true;
                this.props.setUserList(userList);
                break;
            }
        }
    }

    /**
     * After answering the phone, send an answer to confirm the message, display the media panel
     */
    handleOk = () => {
        this.setState({
            videoCallModal: false,
        })
        let data = {
            contentType: Constant.ACCEPT_VIDEO_ONLINE,
            type: Constant.MESSAGE_TRANS_TYPE,
            toUser: this.state.fromUserUuid,
        }
        this.sendMessage(data);

        let media = {
            ...this.props.media,
            showMediaPanel: true,
        }
        this.props.setMedia(media)
    }

    handleCancel = () => {
        let data = {
            contentType: Constant.REJECT_VIDEO_ONLINE,
            type: Constant.MESSAGE_TRANS_TYPE,
        }
        this.sendMessage(data);
        this.setState({
            videoCallModal: false,
        })
    }

    dealMediaCall = (message) => {
        if (message.contentType === Constant.DIAL_AUDIO_ONLINE || message.contentType === Constant.DIAL_VIDEO_ONLINE) {
            this.setState({
                videoCallModal: true,
                callName: message.fromUsername,
                fromUserUuid: message.from,
            })
            return;
        }

        if (message.contentType === Constant.CANCELL_AUDIO_ONLINE || message.contentType === Constant.CANCELL_VIDEO_ONLINE) {
            this.setState({
                videoCallModal: false,
            })
            return;
        }

        if (message.contentType === Constant.REJECT_AUDIO_ONLINE || message.contentType === Constant.REJECT_VIDEO_ONLINE) {
            let media = {
                ...this.props.media,
                mediaReject: true,
            }
            this.props.setMedia(media);
            return;
        }

        if (message.contentType === Constant.ACCEPT_VIDEO_ONLINE || message.contentType === Constant.ACCEPT_AUDIO_ONLINE) {
            let media = {
                ...this.props.media,
                mediaConnected: true,
            }
            this.props.setMedia(media);
        }
    }

    render() {

        return (
            <>
                <Row style={{ paddingTop: 35, borderBottom: '1px solid #52c41a', borderTop: '1px solid #52c41a' }}>
                    <Col span={2} style={{ borderRight: '1px solid #52c41a', textAlign: 'center', borderTop: '1px solid #52c41a' }}>
                        <Left history={this.props.history} />
                    </Col>

                    <Col span={4} style={{ borderRight: '1px solid #52c41a', borderTop: '1px solid #52c41a' }}>
                        <Center />
                    </Col>

                    <Col offset={1} span={16} style={{ borderTop: '1px solid #52c41a' }}>
                        <Right
                            history={this.props.history}
                            sendMessage={this.sendMessage}
                            checkMediaPermisssion={this.checkMediaPermisssion}
                        />
                    </Col>
                </Row>


                <Drawer width='820px' forceRender={true} title="Media panel" placement="right" onClose={this.mediaPanelDrawerOnClose} visible={this.props.media.showMediaPanel}>
                    <Tooltip title="End video voice">
                        <Button
                            shape="circle"
                            onClick={this.stopVideoOnline}
                            style={{ marginRight: 10, float: 'right' }}
                            icon={<PoweroffOutlined style={{ color: 'red' }} />}
                        />
                    </Tooltip>
                    <br />
                    <video id="localVideoReceiver" width="700px" height="auto" autoPlay muted controls />
                    <video id="remoteVideoReceiver" width="700px" height="auto" autoPlay muted controls />

                    <img id="receiver" width={this.state.currentScreen.width} height="auto" alt="" />
                    <canvas id="canvas" width={this.state.currentScreen.width} height={this.state.currentScreen.height} />
                    <audio id="audioPhone" autoPlay controls />
                </Drawer>

                <Modal
                    title="video call"
                    visible={this.state.videoCallModal}
                    onOk={this.handleOk}
                    onCancel={this.handleCancel}
                    okText="Answer"
                    cancelText="hang up"
                >
                    <p>{this.state.callName}Call</p>
                </Modal>
            </>
        );
    }
}

function mapStateToProps(state) {
    return {
        user: state.userInfoReducer.user,
        media: state.panelReducer.media,
        messageList: state.panelReducer.messageList,
        chooseUser: state.panelReducer.chooseUser,
        peer: state.panelReducer.peer,
        userList: state.panelReducer.userList,
    }
}

function mapDispatchToProps(dispatch) {
    return {
        setUserList: (data) => dispatch(actions.setUserList(data)),
        setMessageList: (data) => dispatch(actions.setMessageList(data)),
        setSocket: (data) => dispatch(actions.setSocket(data)),
        setMedia: (data) => dispatch(actions.setMedia(data)),
    }
}

Panel = connect(mapStateToProps, mapDispatchToProps)(Panel)

export default Panel