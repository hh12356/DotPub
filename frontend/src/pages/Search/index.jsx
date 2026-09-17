import { Card, Input,Listy, Empty } from 'antd';
import './index.scss';
import { useNavigate,  useSearchParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { ArtSrchAPI } from '@/apis/article';
import ArticleCard from '@/components/ArticleCard';
import { useArticles } from '@/hooks/useArticles';

const Search = () => {

    const [searchParams] = useSearchParams()
    const q = searchParams.get('q')||''

    const navigate = useNavigate()
    const onSearch = (value)=>{
        navigate(`/search?q=${encodeURIComponent(value)}`)
    }

    const [article,setArticle] = useState([])

    
    //没搜索词时的兜底列表
    const { articles: latest } = useArticles('hot')

    useEffect(()=>{
        if(!q) return
        //q 一变 React 会先跑上一次的 cleanup，把 cancelled 置为 true，
        //旧请求返回时就知道自己已经过时，不会覆盖掉新关键词的结果
        let cancelled = false
        const fetchSrch = async ()=>{
            const res = await ArtSrchAPI(q)
            if(!cancelled) setArticle(res.data)
        }
        fetchSrch()
        return ()=>{ cancelled = true }
    },[q])

    const list = q?article:latest

    return (
        <div id='search'>
            <div className='search-bar'>
                <Input.Search placeholder='搜索文章' size='large' onSearch={onSearch}/>
            </div>

            {q&&article.length===0?
            <Empty description='空空如也' style={{marginTop:80}}/>:
            <Listy
                items={list}
                rowKey="art_id"
                styles={{item:{borderBottom:'none'}}}
                itemRender={(item) => <ArticleCard article={item} />}
            />}
        </div>
    )
}

export default Search;
