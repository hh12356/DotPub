import { Button, Form, Input, message } from 'antd';
import './index.scss'
import { useEffect, useState } from 'react';
import { loginAPI } from '@/apis/login';

const Login = ()=>{
    const [userName,setUserName] = useState("")
    const [userPassword,setUserPassword] = useState("")

    const userNameChange = (value)=>{
        setUserName(value)
    }
    const userPasswordChange = (value)=>{
        setUserPassword(value)
    }

    const submit = async ()=>{
        const res = await loginAPI({
            "user_name":userName,
            "user_pwd":userPassword
        })
        const data = res.data
        console.log(data);
        if(res.data.code=="200"){
            message.success(data.msg)
        }
        else{
            message.error(data.msg)
        }
    }

    return (
        <div id='container'>
            <Form>
                <Form.Item
                name="username"
                rules={[{ required: true, message: 'Please input your username!' }]}
                >
                <Input variant='filled' placeholder='用户名' value={userName} onChange={(e)=>userNameChange(e.target.value)}/>
                </Form.Item>

                <Form.Item
                name="password"
                rules={[{ required: true, message: 'Please input your password!' }]}
                >
                <Input.Password  variant='filled' placeholder='密码' value={userPassword} onChange={(e)=>userPasswordChange(e.target.value)}/>
                </Form.Item>

                <Form.Item>
                <Button type="primary" htmlType="submit" onClick={submit}>
                    提交
                </Button>
                </Form.Item>
            </Form>
        </div>
    )
}

export default Login