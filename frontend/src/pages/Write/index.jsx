import { Button, Form, Input, message } from 'antd';
import ReactQuill from 'react-quill-new';
import 'react-quill-new/dist/quill.snow.css';
import './index.scss';
import { ArtSubmitAPI } from '@/apis/article';
import { useNavigate } from 'react-router-dom';
import { getToken, removeToken } from '@/utils/token';
import { removeUserName } from '@/utils/userName';
import { useEffect, useState } from 'react';

const Write = () => {
    const navigate = useNavigate()

    // Quill 的空内容是 <p><br></p> 而不是空串，required 规则抓不到；纯图片也算有内容
    const isEmptyHtml = (html) =>
        !html || (html.replace(/<[^>]*>/g, '').trim() === '' && !/<(img|video|iframe)\b/i.test(html));

    const onFinish = async (values) => {
        if(!notLogin){
            //校验正文是否为空
            if (isEmptyHtml(values.art_content)) {
                message.error('请输入正文');
                return;
            }
            //提交至后端
            try{
                await ArtSubmitAPI(values)
                message.success('上传成功')
                navigate('/')
                //缺少高亮切换
            }
            catch(e){
                message.error(e.response?.data?.detail?.msg||"请求失败，请稍后重试")
            }
        }
        else{
            navigate('/login')
        }
    };

    const notLogin = !getToken()

    return (
        <div id="write-container">
            <div id='blank'></div>
            <Form onFinish={onFinish}>
                <Form.Item
                    name="art_title"
                    rules={[{ required: !notLogin, message: '请输入标题' }]}
                >
                    <Input variant="filled" placeholder={!notLogin&&'标题'} disabled={notLogin}/>
                </Form.Item>

                <Form.Item name="art_content" className="editor-item">
                    <ReactQuill theme="snow" placeholder={notLogin?'未登录':"正文"} readOnly={notLogin}/>
                </Form.Item>

                <Form.Item>
                    <Button type="primary" htmlType="submit">
                        {notLogin?'去登录':'提交'}
                    </Button>
                </Form.Item>
            </Form>
        </div>
    );
};

export default Write;
