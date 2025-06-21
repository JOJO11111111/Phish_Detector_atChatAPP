import React from 'react';
import {
    Row,
    Button,
    Col,
    Menu,
    Modal,
    Dropdown,
    Input,
    Form,
    message
} from 'antd';
import { PlusCircleOutlined } from '@ant-design/icons';
import { connect } from 'react-redux';
import { actions } from '../../../redux/module/panel';
import * as Params from '../../../common/param/Params';
import { axiosGet, axiosPostBody } from '../../../util/Request';

class UserSearch extends React.Component {
    groupForm = React.createRef();
    constructor(props) {
        super(props)
        this.state = {
            showCreateGroup: false,
            hasUser: false,
            queryUser: {
                username: '',
                nickname: '',
            },
        }
    }

    searchUser = (value, _event) => {
        if (!value) return;

        const data = { name: value };
        axiosGet(Params.USER_NAME_URL, data)
            .then(response => {
                const data = response.data;
                if (!data.user.username && !data.group.name) {
                    message.error("No group or user found");
                    return;
                }
                const queryUser = {
                    username: data.user.username,
                    nickname: data.user.nickname,
                    groupUuid: data.group.uuid,
                    groupName: data.group.name,
                };
                this.setState({ hasUser: true, queryUser });
            });
    }

    showModal = () => this.setState({ hasUser: true });
    
    addUser = () => {
        const data = {
            uuid: localStorage.uuid,
            friendUsername: this.state.queryUser.username
        };
        axiosPostBody(Params.USER_FRIEND_URL, data)
            .then(() => {
                message.success("User added successfully");
                this.setState({ hasUser: false });
            });
    };

    joinGroup = () => {
        axiosPostBody(`${Params.GROUP_JOIN_URL}${localStorage.uuid}/${this.state.queryUser.groupUuid}`)
            .then(() => {
                message.success("Joined group successfully");
                this.setState({ hasUser: false });
            });
    }

    handleCancel = () => this.setState({ hasUser: false });
    showCreateGroup = () => this.setState({ showCreateGroup: true });
    handleCancelGroup = () => this.setState({ showCreateGroup: false });

    createGroup = () => {
        const values = this.groupForm.current.getFieldValue();
        const data = { name: values.groupName };
        axiosPostBody(`${Params.GROUP_LIST_URL}/${localStorage.uuid}`, data)
            .then(() => {
                message.success("Group created successfully");
                this.setState({ showCreateGroup: false });
            });
    }

    render() {
        const menu = (
            <Menu>
                <Menu.Item key="1">
                    <Button type='link' onClick={this.showModal}>Add User</Button>
                </Menu.Item>
                <Menu.Item key="2">
                    <Button type='link' onClick={this.showModal}>Add to Group</Button>
                </Menu.Item>
                <Menu.Item key="3">
                    <Button type='link' onClick={this.showCreateGroup}>Create Group</Button>
                </Menu.Item>
            </Menu>
        );

        return (
            <>
                <Row style={{ marginBottom: 16 }}>
                    <Col span={20}>
                        <Input.Group compact>
                            <Input.Search
                                allowClear
                                style={{ width: '100%', borderColor: '#52c41a' }}
                                onSearch={this.searchUser}
                                placeholder="Search by username"
                            />
                        </Input.Group>
                    </Col>
                    <Col>
                        <Dropdown overlay={menu} placement="bottomCenter" arrow>
                            <PlusCircleOutlined style={{ fontSize: 24, color: '#52c41a', marginLeft: 8 }} />
                        </Dropdown>
                    </Col>
                </Row>

                <Modal
                    title="User Information"
                    visible={this.state.hasUser}
                    onCancel={this.handleCancel}
                    footer={null}
                >
                    <Input.Group compact>
                        <Input.Search
                            allowClear
                            style={{ width: '100%', borderColor: '#52c41a' }}
                            onSearch={this.searchUser}
                            placeholder="Search for another user"
                        />
                    </Input.Group>
                    <div style={{ marginTop: 16 }}>
                        <p><strong>Username:</strong> {this.state.queryUser.username}</p>
                        <p><strong>Nickname:</strong> {this.state.queryUser.nickname}</p>
                        <Button
                            type='primary'
                            style={{ backgroundColor: '#52c41a', borderColor: '#52c41a', color: 'white' }}
                            onClick={this.addUser}
                            disabled={!this.state.queryUser.username}
                        >
                            Add User
                        </Button>
                    </div>
                    <div style={{ marginTop: 16, borderTop: '1px solid #f0f0f0', paddingTop: 16 }}>
                        <p><strong>Group:</strong> {this.state.queryUser.groupName}</p>
                        <Button
                            type='primary'
                            style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' ,color: 'white'}}
                            onClick={this.joinGroup}
                            disabled={!this.state.queryUser.groupUuid}
                        >
                            Join Group
                        </Button>
                    </div>
                </Modal>

                <Modal
                    title="Create Group"
                    visible={this.state.showCreateGroup}
                    onCancel={this.handleCancelGroup}
                    onOk={this.createGroup}
                    okText="Create"
                    okButtonProps={{ style: { backgroundColor: '#52c41a', borderColor: '#52c41a' } }}
                >
                    <Form
                        name="groupForm"
                        ref={this.groupForm}
                        layout="vertical"
                        autoComplete="off"
                    >
                        <Form.Item
                            name="groupName"
                            label="Group Name"
                            rules={[{ required: true, message: 'Please enter a group name' }]}
                        >
                            <Input placeholder="Enter group name" />
                        </Form.Item>
                    </Form>
                </Modal>
            </>
        );
    }
}

const mapStateToProps = (state) => ({
    user: state.userInfoReducer.user,
});

const mapDispatchToProps = (dispatch) => ({
    setUser: (data) => dispatch(actions.setUser(data)),
});

export default connect(mapStateToProps, mapDispatchToProps)(UserSearch);


