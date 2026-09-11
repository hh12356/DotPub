import { Button, Form, Input, message } from 'antd';
import ReactQuill from 'react-quill-new';
import 'react-quill-new/dist/quill.snow.css';
import './index.scss';

const Write = () => {
    const onFinish = async (values) => {
        // TODO: 提交 values.title / values.content
        console.log(values);
        message.success('提交成功');
    };

    return (
        <div id="write-container">
            <div id='blank'></div>
            <Form onFinish={onFinish}>
                <Form.Item
                    name="title"
                    rules={[{ required: true, message: '请输入标题' }]}
                >
                    <Input variant="filled" placeholder="标题" />
                </Form.Item>

                <Form.Item name="content" className="editor-item">
                    <ReactQuill theme="snow" placeholder="正文" />
                </Form.Item>

                <Form.Item>
                    <Button type="primary" htmlType="submit">
                        提交
                    </Button>
                </Form.Item>
            </Form>
        </div>
    );
};

export default Write;
