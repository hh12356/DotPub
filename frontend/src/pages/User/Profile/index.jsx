import { UserProfileAPI,UpdateBioAPI } from "@/apis/user"
import ArticleCard from "@/components/ArticleCard"
import { EditOutlined } from "@ant-design/icons"
import { Flex, Input, Result, Statistic, Typography,Listy, message } from "antd"
import { useEffect, useState,useMemo } from "react"
import { useParams } from "react-router-dom"

const vote = (a) => 0.4 * (a.like_count ?? 0) + 0.6 * (a.star_count ?? 0)

const Profile = () => {

    const { id } = useParams()
    const [data, setData] = useState({})
    const [error, setError] = useState(null)
    //编辑简介：editing 决定显示输入框还是文字，draft 是编辑中的草稿
    const [editing, setEditing] = useState(false)
    const [draft, setDraft] = useState('')

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

    //点图标：把当前简介灌进草稿，再切到编辑态
    const onEdit = () => {
        setDraft(data.user_bio)
        setEditing(true)
    }

    const onSave = async () => {
        try {
            await UpdateBioAPI(draft)
            setData({ ...data, user_bio: draft })   //本地先更新，省一次重新拉接口
            setEditing(false)
            message.success("编辑成功")
        } catch {
            //保存失败就留在编辑态：草稿不丢，可以直接重试
        }
    }

    return (
        <div>
            <div style={{ width: '85vw', margin: '24px auto' }}>
                <Typography.Title level={1} style={{ margin: 0 }}>{name}</Typography.Title>
                <Flex align="center" gap={8} style={{ marginTop: 8 }}>
                    {editing
                        ? <Input.TextArea
                            autoFocus
                            autoSize={{ minRows: 2, maxRows: 6 }}
                            maxLength={100}          
                            placeholder="介绍一下自己吧"
                            value={draft}
                            onChange={e => setDraft(e.target.value)}
                            onBlur={onSave}   //点别处就保存
                            style={{ flex: 1 }}   //撑满整行，跟简介、统计、文章列表同宽
                          />
                        : <>
                            {/*pre-wrap 必须加：HTML 默认把换行符当空格折叠掉，
                               不加这行就算存进去了换行也看不出来*/}
                            <Typography.Paragraph type="secondary" style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                                {data.user_bio || '这个人很懒，什么都没写'}
                            </Typography.Paragraph>
                            {data.self && (
                                <EditOutlined style={{ cursor: 'pointer', color: 'rgba(0,0,0,0.45)' }} onClick={onEdit}/>
                            )}
                          </>}
                </Flex>
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
