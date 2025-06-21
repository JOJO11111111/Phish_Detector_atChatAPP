import React from 'react';

import {
    Tag,
    Tooltip,
    Button
} from 'antd';

import {
    SyncOutlined,
    UngroupOutlined
} from '@ant-design/icons';

import ChatDetails from './component/ChatDetails';
import ChatFile from './component/ChatFile';
import ChatAudio from './component/ChatAudio';
import ChatVideo from './component/ChatVideo';
import ChatShareScreen from './component/ChatShareScreen';
import ChatAudioOline from './component/ChatAudioOline';
import ChatVideoOline from './component/ChatVideoOline';
import ChatEdit from './component/ChatEdit';

import moment from 'moment';
import { connect } from 'react-redux';
import { actions } from '../../redux/module/panel';

class RightIndex extends React.Component {

    /**
     * Add the message to the message panel
     * @param {Message content, including picture video message label} content 
     */
    appendMessage = (content) => {
        let messageList = [
            ...this.props.messageList,
            {
                author: localStorage.username,
                avatar: this.props.user.avatar,
                content: <p>{content}</p>,
                datetime: moment().fromNow(),
            },
        ];
        this.props.setMessageList(messageList);
    }

    /**
     * After uploading the local area, add the picture to the chat box
     * @param {ArrayBuffer type image}} imgData 
     */
    appendImgToPanel(imgData) {
        // Convert ArrayBuffer to Base64 for display
        var binary = '';
        var bytes = new Uint8Array(imgData);
        var len = bytes.byteLength;
        for (var i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        let base64String = `data:image/jpeg;base64,${window.btoa(binary)}`;

        this.appendMessage(<img src={base64String} alt="" width="150px" />);
    }

    showMediaPanel = () => {
        let media = {
            ...this.props.media,
            showMediaPanel: true,
        }
        this.props.setMedia(media)
    }

    render() {

        return (
            <div style={{
                height: document.body.scrollHeight - 80,
                overflow: 'hidden',
            }}
            >
                <ChatDetails history={this.props.history} appendMessage={this.appendMessage} />
                <br />
                <ChatFile
                    history={this.props.history}
                    appendMessage={this.appendMessage}
                    appendImgToPanel={this.appendImgToPanel}
                    sendMessage={this.props.sendMessage}
                />
                <ChatAudio
                    history={this.props.history}
                    appendMessage={this.appendMessage}
                    sendMessage={this.props.sendMessage}
                />

                <ChatVideo
                    history={this.props.history}
                    appendMessage={this.appendMessage}
                    sendMessage={this.props.sendMessage}
                    checkMediaPermisssion={this.props.checkMediaPermisssion}
                />

                <ChatShareScreen
                    history={this.props.history}
                    sendMessage={this.props.sendMessage}
                    checkMediaPermisssion={this.props.checkMediaPermisssion}
                />

                <ChatAudioOline
                    history={this.props.history}
                    sendMessage={this.props.sendMessage}
                    checkMediaPermisssion={this.props.checkMediaPermisssion}
                />

                <ChatVideoOline
                    history={this.props.history}
                    sendMessage={this.props.sendMessage}
                    checkMediaPermisssion={this.props.checkMediaPermisssion}
                />

                <Tooltip title="Display video panel">
                    <Button
                        shape="circle"
                        onClick={this.showMediaPanel}
                        style={{ marginRight: 10 }}
                        icon={<UngroupOutlined />}
                    />
                </Tooltip>

                <Tag icon={<SyncOutlined spin />} color="processing" hidden={!this.props.media.isRecord}>
                    Recording
                </Tag>

                <ChatEdit
                    history={this.props.history}
                    appendMessage={this.appendMessage}
                    appendImgToPanel={this.appendImgToPanel}
                    sendMessage={this.props.sendMessage}
                />

            </div>
        );
    }
}

function mapStateToProps(state) {
    return {
        user: state.userInfoReducer.user,
        media: state.panelReducer.media,
        chooseUser: state.panelReducer.chooseUser,
        messageList: state.panelReducer.messageList,
        socket: state.panelReducer.socket,
    }
}

function mapDispatchToProps(dispatch) {
    return {
        setMessageList: (data) => dispatch(actions.setMessageList(data)),
        setMedia: (data) => dispatch(actions.setMedia(data)),
    }
}

RightIndex = connect(mapStateToProps, mapDispatchToProps)(RightIndex)

export default RightIndex