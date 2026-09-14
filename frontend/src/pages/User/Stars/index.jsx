import { UserStarsAPI } from "@/apis/user"
import ArticleCard from "@/components/ArticleCard"
import { Empty,Listy,Typography } from "antd"
import { useEffect, useState } from "react"


const Stars = ()=>{

    const [articles,setArticles] = useState([])
    useEffect(()=>{
        const fetchStars = async ()=>{
            const res = await UserStarsAPI()
            setArticles(res.data)
        }
        fetchStars()
    },[])

    return (
    <div>
        {articles.length>0&&
        <div style={{width:'85vw',margin:'0 auto 18px',marginTop:'10px',marginBottom:'2px'}}>
            <Typography.Text type="secondary">共 {articles.length} 篇文章</Typography.Text>
        </div>}

        {articles.length===0?
        <Empty description='空空如也' style={{marginTop:80}}/>:
        <Listy
            items={articles}
            rowKey="art_id"
            styles={{item:{borderBottom:'none'}}}
            itemRender={(item) => <ArticleCard article={item} />}
        />}
    </div>
)
}

export default Stars;
