import { request } from "@/utils"

//注册请求
export function signupAPI(userData){
    const {user_name,user_phone,user_pwd} = userData
    return request({
        url:'/signup',
        method:'POST',
        data:{user_phone,user_name,user_pwd}
    })
}