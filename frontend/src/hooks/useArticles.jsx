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

export {useArticles}