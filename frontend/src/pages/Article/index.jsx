import { ArtGetAPI, ArtLikeAPI, ArtUnlikeAPI,ArtStarAPI,ArtUnStarAPI } from '@/apis/article';
import { HeartOutlined, StarOutlined,HeartFilled,StarFilled } from '@ant-design/icons';
import { Button, message, Typography } from 'antd';
import DOMPurify from 'dompurify';
import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import 'react-quill-new/dist/quill.core.css';
import './index.scss';

const formatDate = (iso) =>
    iso ? new Date(iso).toLocaleDateString('zh-CN', { dateStyle: 'long' }) : '';

const Article = () => {
    const params = useParams();
    const art_id = Number(params.id);
    const [article, setArticle] = useState({});

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

    return (
        <article id="article-page">
            <Typography.Title level={1}>{article.art_title}</Typography.Title>

            <div className="article-meta">
                <span>{article.art_author}</span>
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
            </div>
        </article>
    );
};

export default Article;