import { request } from "@/utils"

//上传文章请求
export function ArtSubmitAPI(ArtData){
    return request({
        url:'/article',
        method:'POST',
        data:ArtData
    })
}

//获取所有文章请求
export function ArtGetAllAPI(){
    return request({
        url:'/article',
        method:'GET'
    })
}

//获取对应id文章请求
export function ArtGetAPI(id){
    return request({
        url:`/article/${id}`,
        method:'GET'
    })
}

//获编辑文章请求
export function ArtEditAPI(id,ArtDate){
    return request({
        url:`/article/${id}`,
        method:'PUT',
        data:ArtDate
    })
}

//删除文章请求
export function ArtDelAPI(id){
    return request({
        url:`/article/${id}`,
        method:'DELETE'
    })
}

//点赞文章
export function ArtLikeAPI(id){
    return request({
        url:`/like/${id}`,
        method:'GET'
    })
}

//取消点赞
export function ArtUnlikeAPI(id){
    return request({
        url:`/like/${id}`,
        method:'DELETE'
    })
}


//收藏文章
export function ArtStarAPI(id){
    return request({
        url:`/star/${id}`,
        method:'GET'
    })
}

//取消收藏
export function ArtUnStarAPI(id){
    return request({
        url:`/star/${id}`,
        method:'DELETE'
    })
}

//取消收藏
export function ArtSrchAPI(q){
    return request({
        url:`/search/${q}`,
        method:'GET'
    })
}

//发布评论
export function ArtCmtAPI(q,cmt){
    return request({
        url:`/comment/${q}`,
        method:'PUT',
        data:{"cmt_content":cmt}
    })
}

//拉取评论
export function ArtGetCmtAPI(q){
    return request({
        url:`/comment/${q}`,
        method:'GET',
    })
}

//删除评论
export function ArtDelCmtAPI(cmt_id){
    return request({
        url:`/comment/${cmt_id}`,
        method:'DELETE'
    })
}