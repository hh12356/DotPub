import { request } from "@/utils";

//获取所有文章请求
export function AdminGetData(){
    return request({
        url:'/admin/stats',
        method:'GET'
    })
}