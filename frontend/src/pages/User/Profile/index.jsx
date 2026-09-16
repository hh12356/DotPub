import { UserProfileAPI,UpdateBioAPI,BanUserAPI,SilenceUserAPI } from "@/apis/user"
import ArticleCard from "@/components/ArticleCard"
import { EditOutlined } from "@ant-design/icons"
import { Button, Flex, Input, Popconfirm, Result, Statistic, Typography,Listy, message } from "antd"
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
        } 
        catch (e) {
            if(e.response?.status !== 401){
                message.error(e.response?.data?.detail?.msg||"请求失败，请稍后重试")
            }
        }
    }

    //封号/解封，next 是目标状态（true=封，false=解封）
    const onBan = async (next) => {
        try {
            const res = await BanUserAPI(id, next)
            setData({ ...data, is_banned: next })
            message.success(res.msg)
        } catch (e) {
            if(e.response?.status !== 401){
                message.error(e.response?.data?.detail?.msg||"请求失败，请稍后重试")
            }
        }
    }

    //禁言/解除禁言，next 是目标状态（true=禁言，false=解除）
    const onSilence = async (next) => {
        try {
            const res = await SilenceUserAPI(id, next)
            setData({ ...data, is_muted: next })
            message.success(res.msg)
        } catch (e) {
            if(e.response?.status !== 401){
                message.error(e.response?.data?.detail?.msg||"请求失败，请稍后重试")
            }
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
                            onBlur={onSave}  
                            style={{ flex: 1 }}   
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

                {/* 拉黑操作：只有管理员看得到，且不能操作自己（封了自己就登不进来了） */}
                {data.can_ban && !data.self && (
                    <Flex gap={8} style={{ marginTop: 12 }}>
                        <Popconfirm
                            title={data.is_banned ? '确定解封该用户？' : '确定封号？封号后该用户无法登录'}
                            onConfirm={() => onBan(!data.is_banned)}
                        >
                            <Button danger size="small">
                                {data.is_banned ? '解封' : '封号'}
                            </Button>
                        </Popconfirm>
                        <Popconfirm
                            title={data.is_muted ? '确定解除禁言？' : '确定禁言？禁言后该用户无法进行需要登录的操作'}
                            onConfirm={() => onSilence(!data.is_muted)}
                        >
                            <Button danger size="small">
                                {data.is_muted ? '解除禁言' : '禁言'}
                            </Button>
                        </Popconfirm>
                    </Flex>
                )}

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
