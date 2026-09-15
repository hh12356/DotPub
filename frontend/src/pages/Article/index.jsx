import { ArtGetAPI, ArtLikeAPI, ArtUnlikeAPI,ArtStarAPI,ArtUnStarAPI, ArtDelAPI, ArtCmtAPI, ArtGetCmtAPI, ArtDelCmtAPI } from '@/apis/article';
import { DeleteOutlined, HeartOutlined, StarOutlined,HeartFilled,StarFilled } from '@ant-design/icons';
import { Button, Empty, Input, Listy, message, Popconfirm, Typography } from 'antd';
import DOMPurify from 'dompurify';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import 'react-quill-new/dist/quill.core.css';
import './index.scss';

const formatDate = (iso) =>
    iso ? new Date(iso).toLocaleDateString('zh-CN', { dateStyle: 'long' }) : '';

const Article = () => {
    const params = useParams();
    const art_id = Number(params.id);
    const navigate = useNavigate();
    const [article, setArticle] = useState({});
    //comment 是输入框里的草稿，comments 是列表数据（等接口）
    const [comment, setComment] = useState('');
    const [comments, setComments] = useState([]);

    const fetchArticle =useCallback(async () => {
        const res = await ArtGetAPI(art_id);
        setArticle(res.data);
    },[art_id]) 

    useEffect(() => {
        fetchArticle();
    }, [fetchArticle]);

    //点赞收藏
    const OnClickLike = async ()=>{
        try{
            if(!article.is_liked){
                await ArtLikeAPI(art_id)
            }
            else{
                await ArtUnlikeAPI(art_id)
            }
            await fetchArticle()
        }
        catch(e){
            if(e.response?.status !== 401){
                message.error(e.response?.data?.detail?.msg||"请求失败，请稍后重试")
            }
        }
    }
    const OnClickStar = async ()=>{
        try{
            if(!article.is_starred){
                await ArtStarAPI(art_id)
            }
            else{
                await ArtUnStarAPI(art_id)
            }
            await fetchArticle()
        }
        catch(e){
            if(e.response?.status !== 401){
                message.error(e.response?.data?.detail?.msg||"请求失败，请稍后重试")
            }
        }
    }

    //删除文章
    const OnDeleteArticle = async () => {
        try{
            await ArtDelAPI(art_id)
            message.success('删除成功')
            navigate('/')
        }
        catch(e){
            if(e.response?.status !== 401){
                message.error(e.response?.data?.detail?.msg||"请求失败，请稍后重试")
            }
        }
    }

    //拉取评论
    const fetchCmt = async ()=>{
        const res = await ArtGetCmtAPI(art_id)
        setComments(res.data)
    }
    useEffect(()=>{
        fetchCmt()
    },[art_id])

    //发布评论
    const onSubmitComment = async () => {
        await ArtCmtAPI(art_id,comment)
        fetchCmt()
        setComment('')
        message.success('发布成功')
    }

    //删除评论
    const onDeleteCmt = async (cmt_id) => {
        try{
            await ArtDelCmtAPI(cmt_id)
            fetchCmt()
            message.success('删除成功')
        }
        catch(e){
            if(e.response?.status !== 401){
                message.error(e.response?.data?.detail?.msg||"请求失败，请稍后重试")
            }
        }
    }

    const onClickAuthor = ()=>{
        navigate(`/profile/${article.art_author_id}`)
    }

    return (
        <article id="article-page">
            <Typography.Title level={1}>{article.art_title}</Typography.Title>

            <div className="article-meta">
                <span onClick={onClickAuthor} style={{cursor:"pointer"}}>{article.art_author}</span>
                <span>·</span>
                <span>{formatDate(article.art_pub_datetime)}</span>
            </div>

            {/*
              带 ql-editor 是为了复用 Quill 的正文样式（列表序号、对齐、字号）。
              后端入库前已经用 nh3 清洗过一遍，这里再洗一次是纵深防御
            */}
            <div
                className="article-content ql-editor"
                dangerouslySetInnerHTML={{
                    __html: DOMPurify.sanitize(article.art_content || ''),
                }}
            />

            <div className="article-actions">
                <Button icon={article.is_liked?<HeartFilled />:<HeartOutlined />} onClick={OnClickLike}>点赞 {article.like_count ?? 0}</Button>
                <Button icon={article.is_starred?<StarFilled />:<StarOutlined />} onClick={OnClickStar}>收藏 {article.star_count ?? 0}</Button>
                
                {article.can_delete && (
                    <Popconfirm
                        title="确定删除这篇文章吗？"
                        description="评论、点赞、收藏会一起消失，无法恢复"
                        okText="删除"
                        cancelText="取消"
                        onConfirm={OnDeleteArticle}
                    >
                        <Button danger icon={<DeleteOutlined />} style={{ marginLeft: 'auto' }}>删除</Button>
                    </Popconfirm>
                )}
            </div>

            <div className="article-comments">
                <Typography.Title level={4}>评论 {comments.length}</Typography.Title>

                <Input.TextArea
                    rows={3}
                    maxLength={500}
                    placeholder="写下你的想法……"
                    value={comment}
                    onChange={e => setComment(e.target.value)}
                />
                <div className="comment-submit">
                    <Button
                        type="primary"
                        disabled={!comment.trim()}
                        onClick={onSubmitComment}
                    >
                        发布
                    </Button>
                </div>

                {comments.length === 0
                    ? <Empty description="还没有评论" style={{ marginTop: 32 }} />
                    : <Listy
                        items={comments}
                        rowKey={(item)=>item.cmt_id}
                        styles={{ item: { borderBottom: 'none' } }}
                        itemRender={(item) => (
                            <div className="comment-item">
                                <div className="comment-head">
                                    <span className="comment-name">{item.user_name}</span>
                                    <span className="comment-time">{formatDate(item.cmt_pub_datetime)}</span>
                                    {item.can_delete && (
                                        <Popconfirm
                                            title="确定删除这条评论吗？"
                                            okText="删除"
                                            cancelText="取消"
                                            onConfirm={()=>onDeleteCmt(item.cmt_id)}
                                        >
                                            <DeleteOutlined className="comment-delete" />
                                        </Popconfirm>
                                    )}
                                </div>
                                <div className="comment-content">{item.cmt_content}</div>
                            </div>
                        )}
                      />}
            </div>
        </article>
    );
};

export default Article;