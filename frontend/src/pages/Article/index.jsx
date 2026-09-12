import { ArtGetAPI } from '@/apis/article';
import { Typography } from 'antd';
import DOMPurify from 'dompurify';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import 'react-quill-new/dist/quill.core.css';
import './index.scss';

const formatDate = (iso) =>
    iso ? new Date(iso).toLocaleDateString('zh-CN', { dateStyle: 'long' }) : '';

const Article = () => {
    const params = useParams();
    const art_id = Number(params.id);
    const [article, setArticle] = useState({});

    useEffect(() => {
        const fetchArticle = async () => {
            const res = await ArtGetAPI(art_id);
            setArticle(res.data);
        };
        fetchArticle();
    }, [art_id]);

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

              后端入库前已经用 nh3 清洗过一遍，这里再洗一次是纵深防御：
              1. 库里已有的老数据是清洗上线之前存的，脏的还在里面，后端那层救不了
              2. 万一将来多了一条写入路径忘了清洗，这层还能兜住
              3. 别指望它替代后端——攻击者根本不走这个页面
            */}
            <div
                className="article-content ql-editor"
                dangerouslySetInnerHTML={{
                    __html: DOMPurify.sanitize(article.art_content || ''),
                }}
            />
        </article>
    );
};

export default Article;

