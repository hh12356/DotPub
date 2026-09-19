import { request } from "@/utils" 

//AI对话
export function ChatAPI(data){
    return request({ 
        url:'/chat', 
        method:'POST', 
        data, 
        //设置响应时间
        timeout: 40000
     })
}
