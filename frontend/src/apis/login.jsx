import { request } from "@/utils"

//登录请求
export function loginAPI(userData){
    return request({
        url:'/login',
        method:'POST',
        data:userData
    })
}