import { request } from "@/utils"

//上传文章请求
export function ArtSubmitAPI(ArtData){
    return request({
        url:'/article',
        method:'POST',
        data:ArtData
    })
}