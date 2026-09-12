import { ArtGetAllAPI } from '@/apis/article';
import { useArticles } from '@/hooks/useArticles';
import { Card, Listy, Typography } from 'antd';
import { useEffect, useState,useMemo } from 'react';

// 正文是 HTML，取纯文本的第一行做摘要
const firstLine = (html) => {
    // 块级标签先换成换行，否则多个段落会粘成一行
    const withBreaks = (html || '').replace(/<\/(p|div|li|h[1-6])>|<br\s*\/?>/gi, '\n');
    // 交给浏览器解析，实体（&nbsp; &amp; 等）会被自动解码
    const doc = new DOMParser().parseFromString(withBreaks, 'text/html');
    return (doc.body.textContent || '')
        .split('\n')
        .map((line) => line.trim())
        .find(Boolean) || '';
};

const Latest = () => {

    const articles = useArticles()
    const sortedArticles = useMemo(
        () => articles.toSorted((a, b) => new Date(b.art_pub_datetime) - new Date(a.art_pub_datetime)),
        [articles]
    );

    return (
        <Listy
            items={sortedArticles}
            rowKey="art_id"
            styles={{item:{borderBottom:'none'}}}
            itemRender={(item) => (
                <Card 
                hoverable 
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
