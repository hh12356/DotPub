import { loginAPI } from "@/apis/login";
import { signupAPI } from "@/apis/signup";
import { createSlice } from "@reduxjs/toolkit";
import { setToken as _setToken, getToken } from "@/utils/token"
import { setUserName as _setUserName,getUserName } from "@/utils/userName"
import { setUserRole as _setUserRole,getUserRole } from "@/utils/userRole"

const userStore = createSlice({
    name:'user',
    initialState:{
        token:getToken()||'',
        userName:getUserName()||'',
        userRole:getUserRole()||''
    },
    //同步修改方法
    reducers:{
        setToken(state,action){
            state.token=action.payload
        },
        setUserName(state,action){
            state.userName=action.payload
        },
        setUserRole(state,action){
            state.userRole=action.payload
        },
        clearUserInfo(state){
            state.token=''
            state.userName=''
            state.userRole=''
        }
    }
})

const {setToken,setUserName,setUserRole,clearUserInfo} = userStore.actions

//异步方法
const fetchLogin = (userData)=>{
    return async (dispatch)=>{
        const res = await loginAPI(userData)
        dispatch(setToken(res.data.token))
        dispatch(setUserName(res.data.user_name))
        dispatch(setUserRole(res.data.user_role ?? 'user'))
        _setToken(res.data.token)
        _setUserName(res.data.user_name)
        _setUserRole(res.data.user_role ?? 'user')
        return res
    }
}

const fetchSignup = (userData)=>{
    return async (dispatch)=>{
        const res = await signupAPI(userData)
        dispatch(setToken(res.data.token))
        dispatch(setUserName(res.data.user_name))
        //注册接口不返回 role，新号一律是普通用户
        dispatch(setUserRole('user'))
        _setToken(res.data.token)
        _setUserName(res.data.user_name)
        _setUserRole('user')
    }
}

export {fetchLogin,fetchSignup}

const userReducer = userStore.reducer
export default userReducer