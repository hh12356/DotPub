import { loginAPI } from "@/apis/login";
import { signupAPI } from "@/apis/signup";
import { createSlice } from "@reduxjs/toolkit";

const userStore = createSlice({
    name:'user',
    initialState:{
        token:'',
        userInfo:{}
    },
    //同步修改方法
    reducers:{
        setToken(state,action){
            state.token=action.payload
        },
        setUserInfo(state,action){
            state.userInfo=action.payload
        },
        clearUserInfo(state){
            state.token=''
            state.userInfo={}
        }
    }
})

const {setToken,setUserInfo,clearUserInfo} = userStore.actions

//异步方法
const fetchLogin = (userData)=>{
    return async (dispatch)=>{
        const res = await loginAPI(userData)
        dispatch(setToken(res.data.user_id))
    }
}

const fetchSignup = (userData)=>{
    return async (dispatch)=>{
        const res = await signupAPI(userData)
        dispatch(setToken(res.data.user_id))
    }
}

export {fetchLogin,fetchSignup}

const userReducer = userStore.reducer
export default userReducer