//封装和username相关的方法 存 取 删

const userNameKey='user_info_key'

function setUserName(userName){
    localStorage.setItem(userNameKey,userName)
}

function getUserName(){
    return localStorage.getItem(userNameKey)
}

function removeUserName(){
    localStorage.removeItem(userNameKey)
}

export { setUserName,getUserName,removeUserName }