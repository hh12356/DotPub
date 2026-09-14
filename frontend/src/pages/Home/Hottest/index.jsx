import { useArticles } from '@/hooks/useArticles';
import ArticleCard from '@/components/ArticleCard';
import { Listy } from 'antd';
import { useMemo } from 'react';

//Reddit hot 公式：log10(票数) + t / C
//C 就是"保质期"：老 C 秒的文章，需要 10 倍票数才能追平新的
//取 90 天，比 Reddit 原版（12.5 小时）长青得多
const FRESH_WINDOW = 90 * 24 * 3600

//排序抖动：只在"分数接近"的文章之间换位，拉开差距的不受影响
//0.3 ≈ 票数差 2 倍，或发布时间差 27 天
const JITTER = 0.3

//点赞权重0.25，评论权重0.35，收藏权重0.4
const vote = (a) => 0.25 * (a.like_count ?? 0)
    + 0.35 * (a.comment_count ?? 0)
    + 0.4 * (a.star_count ?? 0)

const Hottest = () => {

    const articles = useArticles()

    const sortedArticles = useMemo(() => {
        const now = Date.now() / 1000
        return articles
            .map((a) => ({
                a,
                score: Math.log10(Math.max(vote(a), 1))
                    - (now - Date.parse(a.art_pub_datetime) / 1000) / FRESH_WINDOW
                    + (Math.random() * 2 - 1) * JITTER,
            }))
            .sort((x, y) => y.score - x.score)
            .map(({ a }) => a)
    }, [articles]);

    return (
        <Listy
            items={sortedArticles}
            rowKey="art_id"
            styles={{item:{borderBottom:'none'}}}
            itemRender={(item) => <ArticleCard article={item} />}
        />
    );
};

export default Hottest;
