import React from 'react';
import {
    List,
    Badge,
    Avatar,
} from 'antd';
import {
    FileOutlined,
} from '@ant-design/icons';

import moment from 'moment';
import InfiniteScroll from 'react-infinite-scroll-component';
import { connect } from 'react-redux'
import { actions } from '../../../redux/module/panel'
import * as Params from '../../../common/param/Params'
import { axiosGet } from '../../../util/Request';


class UserList extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            chooseUser: {}
        }
    }

    componentDidMount() {
    }

    /**
     * Select users and get the corresponding message
     * @param {Choice user} value 
     */
    chooseUser = (value) => {
        let chooseUser = {
            toUser: value.uuid,
            toUsername: value.username,
            messageType: value.messageType,
            avatar: value.avatar
        }
        this.fetchMessages(chooseUser);
        this.removeUnreadMessageDot(value.uuid);
    }

    /**
     * Get message
     */
    fetchMessages = (chooseUser) => {
        const { messageType, toUser, toUsername } = chooseUser
        let uuid = localStorage.uuid
        if (messageType === 2) {
            uuid = toUser
        }
        let data = {
            Uuid: uuid,
            FriendUsername: toUsername,
            MessageType: messageType
        }
        axiosGet(Params.MESSAGE_URL, data)
            .then(response => {
                let comments = []
                let data = response.data
                if (null == data) {
                    data = []
                }
                for (var i = 0; i < data.length; i++) {
                    let contentType = data[i].contentType
                    let content = this.getContentByType(contentType, data[i].url, data[i].content)

                    let comment = {
                        author: data[i].fromUsername,
                        avatar: Params.HOST + "/file/" + data[i].avatar,
                        content: <p>{content}</p>,
                        datetime: moment(data[i].createAt).fromNow(),
                        contentType: data[i].contentType,
                        url: data[i].url
                    }
                    comments.push(comment)
                }

                this.props.setMessageList(comments);
                //When setting the selected user information, you need to set the message list first to prevent the message of the message after the sliding to the bottom movement has been completed.
                this.props.setChooseUser(chooseUser);
            });
    }

    /**
     * Labels corresponding to the file type rendering, such as videos, pictures, etc.
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
     * After viewing the message, remove the unreasonable reminder
     * @param {UUID sent to the corresponding personnel} toUuid 
     */
    removeUnreadMessageDot = (toUuid) => {
        let userList = this.props.userList;
        for (var index in userList) {
            if (userList[index].uuid === toUuid) {
                userList[index].hasUnreadMessage = false;
                this.props.setUserList(userList);
                break;
            }
        }
    }

    render() {

        return (
            <>
                <div id="userList" style={{
                    height: document.body.scrollHeight - 125,
                    overflow: 'auto',
                }}>
                    <InfiniteScroll
                        dataLength={this.props.userList.length}
                        scrollableTarget="userList"
                    >
                        <List
                            itemLayout="horizontal"
                            dataSource={this.props.userList}
                            renderItem={item => (
                                <List.Item>
                                    <List.Item.Meta
                                        style={{ paddingLeft: 30 }}
                                        onClick={() => this.chooseUser(item)}
                                        avatar={<Badge dot={item.hasUnreadMessage}><Avatar src={item.avatar} /></Badge>}
                                        title={item.username}
                                        description=""
                                    />
                                </List.Item>
                            )}
                        />
                    </InfiniteScroll>
                </div>
            </>
        );
    }
}


function mapStateToProps(state) {
    return {
        chooseUser: state.panelReducer.chooseUser,
        userList: state.panelReducer.userList,
    }
}

function mapDispatchToProps(dispatch) {
    return {
        setChooseUser: (data) => dispatch(actions.setChooseUser(data)),
        setUserList: (data) => dispatch(actions.setUserList(data)),
        setMessageList: (data) => dispatch(actions.setMessageList(data)),
    }
}

UserList = connect(mapStateToProps, mapDispatchToProps)(UserList)

export default UserList