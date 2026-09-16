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

//修改个人简介请求
export function UpdateBioAPI(user_bio){
    return request({
        url:'/profile/bio',
        method:'PUT',
        data:{user_bio}
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

//封号/解封请求，value 传目标状态：true=封号 false=解封
export function BanUserAPI(id,value){
    return request({
        url:`/ban/${id}`,
        method:'PUT',
        data:{status:value}
    })
}

//禁言/解除禁言请求，value 传目标状态：true=禁言 false=解除
export function SilenceUserAPI(id,value){
    return request({
        url:`/mute/${id}`,
        method:'PUT',
        data:{status:value}
    })
}