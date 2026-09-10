import { loginAPI } from "@/apis/login";
import { signupAPI } from "@/apis/signup";
import { createSlice } from "@reduxjs/toolkit";
import { setToken as _setToken, getToken } from "@/utils/token"
import { setUserName as _setUserName,getUserName } from "@/utils/userInfo"

const userStore = createSlice({
    name:'user',
    initialState:{
        token:getToken()||'',
        userName:getUserName()||''
    },
    //同步修改方法
    reducers:{
        setToken(state,action){
            state.token=action.payload
        },
        setUserName(state,action){
            state.userName=action.payload
        },
        clearUserInfo(state){
            state.token=''
            state.userName=''
        }
    }
})

const {setToken,setUserName,clearUserInfo} = userStore.actions

//异步方法
const fetchLogin = (userData)=>{
    return async (dispatch)=>{
        const res = await loginAPI(userData)
        dispatch(setToken(res.data.token))
        dispatch(setUserName(res.data.user_name))
        _setToken(res.data.token)
        _setUserName(res.data.user_name)
    }
}

const fetchSignup = (userData)=>{
    return async (dispatch)=>{
        const res = await signupAPI(userData)
        dispatch(setToken(res.data.token))
        dispatch(setUserName(res.data.user_name))
        _setToken(res.data.token)
        _setUserName(res.data.user_name)
    }
}

export {fetchLogin,fetchSignup}

const userReducer = userStore.reducer
export default userReducer