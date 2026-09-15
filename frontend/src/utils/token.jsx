//封装和token相关的方法 存 取 删

const tokenkey='token_key'

function setToken(token){
    sessionStorage.setItem(tokenkey,token)
}

function getToken(){
    return sessionStorage.getItem(tokenkey)
}

function removeToken(){
    sessionStorage.removeItem(tokenkey)
}

function getUserId(){
    const token = getToken()
    if(!token) return null
    //JWT 的 payload 段是 base64url：先换回 +/ ，再补 = 到 4 的倍数，atob 才认
    const part = token.split('.')[1].replace(/-/g,'+').replace(/_/g,'/')
    return JSON.parse(atob(part + '='.repeat((4 - part.length % 4) % 4))).user_id
}

export {setToken,getToken,removeToken,getUserId}