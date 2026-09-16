import { useArticles, pinnedFirst } from '@/hooks/useArticles';
import ArticleCard from '@/components/ArticleCard';
import { Listy } from 'antd';
import { useMemo } from 'react';

const Latest = () => {

    const articles = useArticles()
    const sortedArticles = useMemo(
        () => articles.toSorted((a, b) =>
            pinnedFirst(a, b) || new Date(b.art_pub_datetime) - new Date(a.art_pub_datetime)
        ),
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

export default Latest;
