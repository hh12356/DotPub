//封装和username相关的方法 存 取 删

const userNameKey='user_info_key'

function setUserName(userName){
    sessionStorage.setItem(userNameKey,userName)
}

function getUserName(){
    return sessionStorage.getItem(userNameKey)
}

function removeUserName(){
    sessionStorage.removeItem(userNameKey)
}

export { setUserName,getUserName,removeUserName }