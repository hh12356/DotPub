import { useState,useEffect } from "react"
import {ArtGetAllAPI} from '@/apis/article'


function useArticles(){

    const [articleList,setArticleList] = useState([])
    useEffect(()=>{
        const getArticleList = async ()=>{
            const res = await ArtGetAllAPI()
            setArticleList(res.data)
        }
        getArticleList()
    },[])

    return articleList
}

//置顶的永远浮在最前面。三个 Home 页各有各的排序规则，所以这里只负责
//"谁在前"，接在 `||` 前面用：pinnedFirst(a,b) || 本页自己的比较
function pinnedFirst(a, b){
    return (b.is_pinned ? 1 : 0) - (a.is_pinned ? 1 : 0)
}

export {useArticles,pinnedFirst}