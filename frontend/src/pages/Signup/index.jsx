import { Button, Form, Input, message } from 'antd';
import { useNavigate } from 'react-router-dom';

const Signup = ()=>{
    
    const navigate = useNavigate()
    const BackToLogin = ()=>{
        navigate('/login')
    }

    return (
        <div id='container'>
            <Form
                name="basic"
            >
                <Form.Item
                name="user_name"
                rules={[{ required: true, message: 'Please input your username!' }]}
                >
                <Input variant='filled' placeholder='用户名'/>
                </Form.Item>

                <Form.Item
                name="user_pwd"
                rules={[{ required: true, message: 'Please input your password!' }]}
                >
                <Input.Password  variant='filled' placeholder='密码'/>
                </Form.Item>

                <Form.Item >
                <Button type="primary" htmlType="submit">
                    注册
                </Button>

                <Button type="default" style={{marginLeft:8}} onClick={BackToLogin}>
                    返回登录
                </Button>
                </Form.Item>
            </Form>
        </div>
    )
}

export default Signup