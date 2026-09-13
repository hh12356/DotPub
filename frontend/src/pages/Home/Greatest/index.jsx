import { useArticles } from '@/hooks/useArticles';
import ArticleCard from '@/components/ArticleCard';
import { Listy } from 'antd';
import { useMemo } from 'react';

//点赞权重0.4，收藏权重0.6
const vote = (a) => 0.4 * (a.like_count ?? 0) + 0.6 * (a.star_count ?? 0)

const Greatest = () => {

    const articles = useArticles()

    const sortedArticles = useMemo(
        () => [...articles].sort((a, b) => vote(b) - vote(a)),
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
