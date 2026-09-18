//封装和user_role相关的方法 存 取 删

const userRoleKey='user_role'

function setUserRole(userRole){
    sessionStorage.setItem(userRoleKey,userRole)
}

function getUserRole(){
    return sessionStorage.getItem(userRoleKey)
}

function removeUserRole(){
    sessionStorage.removeItem(userRoleKey)
}

export { setUserRole,getUserRole,removeUserRole }
