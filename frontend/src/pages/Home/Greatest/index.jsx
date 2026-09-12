import { useArticles } from '@/hooks/useArticles';
import { Card, Listy, Typography } from 'antd';
import { useMemo } from 'react';
import { firstLine } from '@/utils/html_process';
import { useNavigate } from 'react-router-dom';

const Greatest = () => {

    const articles = useArticles()
    //当前为随机算法
    const sortedArticles = useMemo(
    () => [...articles].sort(() => Math.random() - 0.5),
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
                title={item.art_title}
                onClick={()=>navigate(`/article/${item.art_id}`)}
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

export default Greatest;
