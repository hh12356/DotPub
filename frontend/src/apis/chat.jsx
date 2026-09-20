import { getToken, removeToken } from "@/utils/token"
import { removeUserName } from "@/utils/userName"
import router from "@/router"

//用request用不了流式显示
export async function ChatStream({ question, art_id, history }, onText) {
    const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ question, art_id, history }),
    })

    //拦截器没了，这里补上
    if (!res.ok) {
        //未登录
        if (res.status === 401) {          
            removeToken(); 
            removeUserName(); 
            router.navigate('/login')
        }
        const body = await res.json().catch(() => null)
        throw new Error(body?.detail?.msg || '请求失败，请稍后重试')
    }

    //创建流读取器，可以流式拉取
    const reader = res.body.getReader()
    //用于将二进制小块转换成utf8文本
    const decoder = new TextDecoder()
    //解码后的字符串缓冲区
    let buf = ''
    //循环拉取
    while (true) {
        //只有这一句会抛浏览器的英文网络错，单独翻译一下，msg.e 那边的 throw 不受影响
        const { done, value } = await reader.read().catch(() => { throw new Error('连接断了，重问一次试试') })
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const frames = buf.split('\n\n')
        //取出最后一个元素放回buf，因为不完整，无法处理
        buf = frames.pop()
        //处理完整数据
        for (const frame of frames) {
            //不以data开头就跳过
            if (!frame.startsWith('data: ')) continue
            //删掉'data: '六字前缀
            const payload = frame.slice(6)
            //结束
            if (payload === '[DONE]') return
            //json转为js对象
            const msg = JSON.parse(payload)
            //e表示错误信息
            if (msg.e) throw new Error(msg.e)
            //使用回调函数追加
            if (msg.t) onText(msg.t)
        }
    }
}