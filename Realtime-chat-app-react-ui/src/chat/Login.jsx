import React from 'react';
import {
    Button,
    Form,
    Input,
    message,
    Typography
} from 'antd';
import { axiosPostBody } from './util/Request';
import * as Params from './common/param/Params';
import './Login.css'; // For custom styling

const { Title, Text } = Typography;

class Login extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            isRegistering: false
        }
    }

    onFinish = (values) => {
        let data = {
            username: values.username,
            password: values.password
        }
        axiosPostBody(Params.LOGIN_URL, data)
            .then(response => {
                message.success("Log in success!");
                localStorage.username = response.data.username;
                this.props.history.push("panel/" + response.data.uuid);
            });
    };

    onFinishFailed = (errorInfo) => {
        console.log('Failed:', errorInfo);
    };

    onRegister = (values) => {
        let data = {
            ...values
        }

        axiosPostBody(Params.REGISTER_URL, data)
            .then(_response => {
                message.success("Successful registration!");
                this.setState({
                    isRegistering: false
                });
            });
    }

    switchToRegister = () => {
        this.setState({
            isRegistering: true
        });
    }

    switchToLogin = () => {
        this.setState({
            isRegistering: false
        });
    }

    render() {
        return (
            <div className="login-container">
                <div className="login-form-container">
                    {this.state.isRegistering ? (
                        <>
                            <Title level={3} style={{ textAlign: 'center', color: '#52c41a' }}>Register</Title>
                            <Text type="secondary" style={{ textAlign: 'center', display: 'block', marginBottom: '20px' }}>Create a new account</Text>
                            <Form
                                name="register"
                                labelCol={{ span: 8 }}
                                wrapperCol={{ span: 16 }}
                                onFinish={this.onRegister}
                                autoComplete="off"
                            >
                                <Form.Item
                                    label="Username"
                                    name="username"
                                    rules={[{ required: true, message: 'Please input your username!' }]}
                                >
                                    <Input placeholder="Choose a username" />
                                </Form.Item>

                                <Form.Item
                                    label="Password"
                                    name="password"
                                    rules={[{ required: true, message: 'Please input your password!' }]}
                                >
                                    <Input.Password placeholder="Create a password" />
                                </Form.Item>

                                <Form.Item
                                    label="Email"
                                    name="email"
                                    rules={[{ required: true, message: 'Please input your email!' }]}
                                >
                                    <Input placeholder="Enter your email" />
                                </Form.Item>

                                <Form.Item
                                    label="Nickname"
                                    name="nickname"
                                    rules={[{ required: true, message: 'Please input your nickname!' }]}
                                >
                                    <Input placeholder="Choose a nickname" />
                                </Form.Item>

                                <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
                                    <Button type="primary" htmlType="submit" block style={{ backgroundColor: '#52c41a', border: 'none' }}>
                                        Register
                                    </Button>
                                </Form.Item>

                                <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
                                    <Text type="secondary">Already have an account?</Text>
                                    <Button type="link" onClick={this.switchToLogin} style={{ paddingLeft: '5px' }}>
                                        Log in here
                                    </Button>
                                </Form.Item>
                            </Form>
                        </>
                    ) : (
                        <>
                            <Title level={3} style={{ textAlign: 'center', color: '#52c41a' }}>Welcome Back</Title>
                            <Text type="secondary" style={{ textAlign: 'center', display: 'block', marginBottom: '20px' }}>Log in to continue</Text>
                            <Form
                                name="login"
                                labelCol={{ span: 8 }}
                                wrapperCol={{ span: 16 }}
                                onFinish={this.onFinish}
                                onFinishFailed={this.onFinishFailed}
                                autoComplete="off"
                            >
                                <Form.Item
                                    label="Username"
                                    name="username"
                                    rules={[{ required: true, message: 'Please input your username!' }]}
                                >
                                    <Input placeholder="Enter your username" />
                                </Form.Item>

                                <Form.Item
                                    label="Password"
                                    name="password"
                                    rules={[{ required: true, message: 'Please input your password!' }]}
                                >
                                    <Input.Password placeholder="Enter your password" />
                                </Form.Item>

                                <Form.Item wrapperCol={{ offset: 6, span: 16}}>
                                    <Button type="primary" htmlType="submit" block style={{ backgroundColor: '#52c41a', border: 'none' }}>
                                        Log in
                                    </Button>
                                </Form.Item>

                                <Form.Item wrapperCol={{ offset: 8, span: 16 }}>
                                    <Text type="secondary">Don't have an account?</Text>
                                    <Button type="link" onClick={this.switchToRegister} style={{ paddingLeft: '5px' }}>
                                        Register Now
                                    </Button>
                                </Form.Item>
                            </Form>
                        </>
                    )}
                </div>
            </div>
        );
    }
}

export default Login;
