import { UserLikesAPI } from "@/apis/user"
import ArticleCard from "@/components/ArticleCard"
import { Empty,Listy,Typography } from "antd"
import { useEffect, useState } from "react"


const Likes = ()=>{

    const [articles,setArticles] = useState([])
    useEffect(()=>{
        const fetchLikes = async ()=>{
            const res = await UserLikesAPI()
            console.log(res.data);
            
            setArticles(res.data)
        }
        fetchLikes()
    },[])

    return (
    <div>
        {/*左边缘和卡片对齐：卡片是 85vw 居中，这里用同样的宽度+自动外边距*/}
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

export default Likes