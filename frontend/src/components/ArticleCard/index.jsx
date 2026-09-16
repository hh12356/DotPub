import { HeartFilled, HeartOutlined, PushpinFilled, StarFilled, StarOutlined } from '@ant-design/icons';
import { Card, Space, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import { firstLine } from '@/utils/html_process';

// Hottest / Latest / Greatest 三个列表共用这一张卡片，
// 样式和字段以后只改这里一处
const ArticleCard = ({ article }) => {
    const navigate = useNavigate();
    const pinned = article.is_pinned;

    return (
        <Card
            hoverable
            title={
                <>
                    {pinned && <PushpinFilled style={{ color: '#4e555e', marginRight: 8 }} />}
                    {article.art_title}
                </>
            }
            onClick={() => navigate(`/article/${article.art_id}`)}
            style={{
                width: '85vw',
                margin: '0 auto',
                //置顶的左边加一条主色竖条，扫列表时一眼能认出来
                ...(pinned && { borderLeft: '3px solid #5a616a' }),
            }}
        >
            <Typography.Paragraph type="secondary">
                {article.art_author}
            </Typography.Paragraph>
            <Typography.Paragraph ellipsis={{ rows: 1 }}>
                {firstLine(article.art_content)}
            </Typography.Paragraph>

            <Space size={16} style={{ fontSize: 13, color: 'rgba(0, 0, 0, 0.45)' }}>
                <span>
                    {article.is_liked?<HeartFilled/>:<HeartOutlined />} {article.like_count ?? 0}
                </span>
                <span>
                    {article.is_starred?<StarFilled/>:<StarOutlined />} {article.star_count ?? 0}
                </span>
            </Space>
        </Card>
    );
};

export default ArticleCard;
