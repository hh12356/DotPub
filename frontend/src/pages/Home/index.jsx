import { useArticles } from '@/hooks/useArticles';
import ArticleCard from '@/components/ArticleCard';
import { Button, Listy } from 'antd';

const Home = ({ sort = 'hot' }) => {

    const { articles, hasMore, loadMore, loading } = useArticles(sort)

    return (
        <>
            <Listy
                items={articles}
                rowKey="art_id"
                styles={{item:{borderBottom:'none'}}}
                itemRender={(item) => <ArticleCard article={item} />}
            />
            {/* hasMore=false 时不渲染，就是到底了 */}
            {hasMore && (
                <div style={{textAlign:'center', margin:16}}>
                    <Button onClick={loadMore} loading={loading}>加载更多</Button>
                </div>
            )}
        </>
    );
};

export default Home;
