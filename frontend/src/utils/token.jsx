//封装和token相关的方法 存 取 删

const tokenkey='token_key'

function setToken(token){
    localStorage.setItem(tokenkey,token)
}

function getToken(){
    return localStorage.getItem(tokenkey)
}

function removeToken(){
    localStorage.removeItem(tokenkey)
}

export {setToken,getToken,removeToken}