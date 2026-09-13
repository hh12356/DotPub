import { LikeOutlined, StarOutlined } from '@ant-design/icons';
import { Card, Space, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import { firstLine } from '@/utils/html_process';

// Hottest / Latest / Greatest 三个列表共用这一张卡片，
// 样式和字段以后只改这里一处
const ArticleCard = ({ article }) => {
    const navigate = useNavigate();

    return (
        <Card
            hoverable
            title={article.art_title}
            onClick={() => navigate(`/article/${article.art_id}`)}
            style={{ width: '85vw', margin: '0 auto' }}
        >
            <Typography.Paragraph type="secondary">
                {article.art_author}
            </Typography.Paragraph>
            <Typography.Paragraph ellipsis={{ rows: 1 }}>
                {firstLine(article.art_content)}
            </Typography.Paragraph>

            <Space size={16} style={{ fontSize: 13, color: 'rgba(0, 0, 0, 0.45)' }}>
                <span>
                    <LikeOutlined /> {article.like ?? 0}
                </span>
                <span>
                    <StarOutlined /> {article.star ?? 0}
                </span>
            </Space>
        </Card>
    );
};

export default ArticleCard;
