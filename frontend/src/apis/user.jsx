import { request } from "@/utils"

//获取用户文章请求
export function UserArtAPI(){
    return request({
        url:'/userart',
        method:'GET'
    })
}

//获取用户信息请求
export function UserProfileAPI(id){
    return request({
        url:   `/profile/${id}`,
        method:'GET'
    })
}


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