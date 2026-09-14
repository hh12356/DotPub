import { UserProfileAPI } from "@/apis/user"
import ArticleCard from "@/components/ArticleCard"
import { Flex, Result, Statistic, Typography,Listy } from "antd"
import { useEffect, useState,useMemo } from "react"
import { useParams } from "react-router-dom"

const vote = (a) => 0.4 * (a.like_count ?? 0) + 0.6 * (a.star_count ?? 0)

const Profile = () => {

    const { id } = useParams()
    const [data, setData] = useState({})
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchData = async () => {
            setError(null)
            try {
                const res = await UserProfileAPI(id)
                setData(res.data)
            } catch (e) {
                setError(e.response?.status === 404 ? '404' : '500')
            }
        }
        fetchData()
    }, [id])
    
    //排序
    const articles = data.art ?? []
    const sortedArticles = useMemo(
        () => [...articles].sort((a, b) => vote(b) - vote(a)),
        [articles]
    );

    if (error) return (
        <Result
            status="error"
            title={error === '404' ? '用户不存在' : '服务器出错了'}
            style={{ marginTop: 80 }}
        />
    )

    const name = data.user_name ?? ''
    if (!name) return null   //还没加载完先不画，省得闪一下

    return (
        <div>
            <div style={{ width: '85vw', margin: '24px auto' }}>
                <Typography.Title level={1} style={{ margin: 0 }}>{name}</Typography.Title>
                <Typography.Paragraph type="secondary" style={{ margin: '8px 0 0' }}>
                    {data.user_bio || '这个人很懒，什么都没写'}
                </Typography.Paragraph>
                <Typography.Text type="secondary" style={{ fontSize: 13 }}>
                    {data.user_join_date?.slice(0, 10)} 加入DotPub
                </Typography.Text>

                <Flex justify="space-around" style={{ marginTop: 32 }}>
                    <Statistic title="发表文章" value={data.art_count} />
                    <Statistic title="获赞" value={data.likes_received} />
                    <Statistic title="被收藏" value={data.stars_received} />
                </Flex>
            </div>
            <Listy
                items={sortedArticles}
                rowKey="art_id"
                styles={{item:{borderBottom:'none'}}}
                itemRender={(item) => <ArticleCard article={item} />}
            />
        </div>
    )
}

export default Profile
