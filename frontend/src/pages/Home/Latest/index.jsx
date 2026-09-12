import { useArticles } from '@/hooks/useArticles';
import { Card, Listy, Typography } from 'antd';
import { useMemo } from 'react';
import { firstLine } from '@/utils/html_process';
import { useNavigate } from 'react-router-dom';

const Latest = () => {

    const articles = useArticles()
    const sortedArticles = useMemo(
        () => articles.toSorted((a, b) => new Date(b.art_pub_datetime) - new Date(a.art_pub_datetime)),
        [articles]
    );

    const navigate = useNavigate()

    return (
        <Listy
            items={sortedArticles}
            rowKey="art_id"
            styles={{item:{borderBottom:'none'}}}
            itemRender={(item) => (
                <Card 
                hoverable 
                onClick={()=>navigate(`/article/${item.art_id}`)}
                title={item.art_title}
                style={{width:"85vw",margin:"0 auto"}}
                >
                    <Typography.Paragraph type="secondary">
                        {item.art_author}
                    </Typography.Paragraph>
                    <Typography.Paragraph ellipsis={{ rows: 1 }}>
                        {firstLine(item.art_content)}
                    </Typography.Paragraph>
                </Card>
            )}
        />
    );
};

export default Latest;
