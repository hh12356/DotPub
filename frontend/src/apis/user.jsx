import { request } from "@/utils"

//获取喜欢请求
export function UserLikesAPI(){
    return request({
        url:'/likes',
        method:'GET'
    })
}

//获取收藏请求
export function UserStarsAPI(){
    return request({
        url:'/stars',
        method:'GET'
    })
}