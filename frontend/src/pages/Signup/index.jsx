import { Button, Form, Input, message } from 'antd';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import {fetchSignup} from "@/store/modules/user"

const Signup = ()=>{
    const [form] = Form.useForm()

    const navigate = useNavigate()
    const BackToLogin = ()=>{
        navigate('/login')
    }

    const dispatch = useDispatch()
    const onFinish = async (values)=>{
        try{
            await dispatch(fetchSignup(values))
            message.success("注册成功")
        }
        catch(e){
            message.error(e.response?.data?.detail?.msg||"请求失败，请稍后重试")
        }
    }

    return (
        <div id='container'>
            <Form
                form={form}
                name='basic'
                validateTrigger="onBlur"
                onFinish={(values)=>onFinish(values)}
            >
                
                <Form.Item
                name="user_phone"
                rules={[
                    { 
                        required: true, 
                        message: '请输入手机号' 
                    },
                    {
                        pattern:/^1[3-9]\d{9}$/,
                        message:'请输入正确的手机号'
                    }]}
                >
                <Input variant='filled' placeholder='手机号'/>
                </Form.Item>

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
                
                <Form.Item
                name="user_pwd_again"
                rules={[
                    {
                     required: true, 
                     message: '请再次输入密码'
                     },
                     {
                     validator: async (_,value)=>{
                        const pwd = form.getFieldValue("user_pwd")
                        if(value&&pwd&&value!==pwd){
                            throw new Error('两次输入密码不一致')
                        }
                     }
                     }
                    ]}
                >
                <Input.Password  variant='filled' placeholder='确认密码'/>
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