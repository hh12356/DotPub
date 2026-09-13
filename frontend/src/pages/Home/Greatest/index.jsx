import { useArticles } from '@/hooks/useArticles';
import ArticleCard from '@/components/ArticleCard';
import { Listy } from 'antd';
import { useMemo } from 'react';

const Greatest = () => {

    const articles = useArticles()
    //当前为随机算法
    const sortedArticles = useMemo(
        () => [...articles].sort(() => Math.random() - 0.5),
        [articles]
    );

    return (
        <Listy
            items={sortedArticles}
            rowKey="art_id"
            styles={{item:{borderBottom:'none'}}}
            itemRender={(item) => <ArticleCard article={item} />}
        />
    );
};

export default Greatest;
