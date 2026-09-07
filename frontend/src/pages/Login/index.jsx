import { Button, Checkbox, Form, Input } from 'antd';
import './index.scss'

const Login = ()=>{
    return (
        <div id='container'>
            <Form
                onFinish
                onFinishFailed
            >
                <Form.Item
                label="用户名"
                name="username"
                rules={[{ required: true, message: 'Please input your username!' }]}
                >
                <Input />
                </Form.Item>

                <Form.Item
                label="密码"
                name="password"
                rules={[{ required: true, message: 'Please input your password!' }]}
                >
                <Input.Password />
                </Form.Item>

                <Form.Item label={null}>
                <Button type="primary" htmlType="submit">
                    提交
                </Button>
                </Form.Item>
            </Form>
        </div>
    )
}

export default Login