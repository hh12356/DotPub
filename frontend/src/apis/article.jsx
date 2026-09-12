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