import { Button, Form, Input, message } from 'antd';
import './index.scss'
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchLogin } from '@/store/modules/user';
import { useDispatch } from 'react-redux';

const Login = ()=>{

    const dispatch = useDispatch()
    const onFinish = async (values)=>{
        try{
            await dispatch(fetchLogin(values))
            message.success('登录成功')
        }
        catch(e){
            message.error(e.response?.data?.detail?.msg||'请求失败，请稍后重试')
        }
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
                <Input variant='filled' placeholder='用户名'/>
                </Form.Item>

                <Form.Item
                name="user_pwd"
                rules={[{ required: true, message: '请输入密码' }]}
                >
                <Input.Password  variant='filled' placeholder='密码'/>
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