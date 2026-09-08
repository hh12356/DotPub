import { Button, Form, Input, message } from 'antd';
import './index.scss'
import { useEffect, useState } from 'react';
import { loginAPI } from '@/apis/login';
import { useNavigate } from 'react-router-dom';

const Login = ()=>{
    const [userName,setUserName] = useState("")
    const [userPwd,setUserPwd] = useState("")

    const userNameChange = (value)=>{
        setUserName(value)
    }
    const userPwdChange = (value)=>{
        setUserPwd(value)
    }

    const onFinish = async (values)=>{
        const res = await loginAPI(values)
        const data = res.data
        message.error(data.msg)
    }

    const navigate = useNavigate()
    const SignUp = ()=>{
        navigate('/signup')
    }

    return (
        <div id='container'>
            <Form 
            validateTrigger={'onBlur'}
            onFinish={(values)=>onFinish(values)}
            >
                <Form.Item
                name="user_name"
                rules={[{ required: true, message: '请输入用户名' }]}
                >
                <Input variant='filled' placeholder='用户名' value={userName} onChange={(e)=>userNameChange(e.target.value)}/>
                </Form.Item>

                <Form.Item
                name="user_pwd"
                rules={[{ required: true, message: '请输入密码' }]}
                >
                <Input.Password  variant='filled' placeholder='密码' value={userPwd} onChange={(e)=>userPwdChange(e.target.value)}/>
                </Form.Item>

                <Form.Item>
                <Button type="primary" htmlType="submit">
                    登录
                </Button>

                <Button type='default' style={{marginLeft:8}} onClick={SignUp}>
                    注册
                </Button>
                </Form.Item>

            </Form>
        </div>
    )
}

export default Login