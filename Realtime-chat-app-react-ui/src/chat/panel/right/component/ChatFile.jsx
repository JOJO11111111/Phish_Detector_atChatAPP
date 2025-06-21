import React from 'react';
import {
    Tooltip,
    Button,
    message
} from 'antd';

import {
    FileAddOutlined,
    FileOutlined
} from '@ant-design/icons';

import { connect } from 'react-redux'
import { actions } from '../../../redux/module/panel'


class ChatFile extends React.Component {
    constructor(props) {
        super(props)
        this.state = {

        }
    }

    componentDidMount() {

    }

    /**
     * Hide the real file upload control, and simulate the click file upload the control through the button
     */
    clickFile = () => {
        let file = document.getElementById("file")
        file.click();
    }

    /**
     * Upload file
     * @param {*} e
     * @returns 
     */
    uploadFile = (e) => {
        let files = e.target.files
        if (!files || !files[0]) {
            return;
        }
        let fileName = files[0].name
        if (null == fileName) {
            message.error("No name")
            return
        }
        let index = fileName.lastIndexOf('.');
        let fileSuffix = null;
        if (index >= 0) {
            fileSuffix = fileName.substring(index + 1);
        }


        let reader = new FileReader()
        reader.onload = ((event) => {
            let file = event.target.result
            // The UINT8 array can intuitively see the value of each byte (1 byte == 8 bits) in ArrayBuffer.Generally, we need to convert ArrayBuffer into a UINT type array before the bytes of them can be accessed.
            // Upload files must be converted to uINT8ARRAY
            var u8 = new Uint8Array(file);

            let data = {
                content: this.state.value,
                contentType: 3,
                fileSuffix: fileSuffix,
                file: u8
            }
            this.props.sendMessage(data)

            if (["jpeg", "jpg", "png", "gif", "tif", "bmp", "dwg"].indexOf(fileSuffix) !== -1) {
                this.props.appendImgToPanel(file)
            } else {
                this.props.appendMessage(<FileOutlined style={{ fontSize: 38 }} />)
            }

        })
        reader.readAsArrayBuffer(files[0])
    }

    render() {
        const { chooseUser } = this.props;
        return (
            <>
                <Tooltip title="Upload pictures or files">
                    <input type='file' id='file' onChange={this.uploadFile} hidden disabled={chooseUser.toUser === ''} />
                    <Button
                        onClick={this.clickFile}
                        shape="circle"
                        style={{ marginRight: 10 }}
                        icon={<FileAddOutlined />}
                        disabled={chooseUser.toUser === ''}
                    />
                </Tooltip>
            </>
        );
    }
}


function mapStateToProps(state) {
    return {
        user: state.userInfoReducer.user,
        chooseUser: state.panelReducer.chooseUser,
        messageList: state.panelReducer.messageList,
        socket: state.panelReducer.socket,
    }
}

function mapDispatchToProps(dispatch) {
    return {
        setMessageList: (data) => dispatch(actions.setMessageList(data)),
    }
}

ChatFile = connect(mapStateToProps, mapDispatchToProps)(ChatFile)

export default ChatFile