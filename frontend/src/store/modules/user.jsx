import { loginAPI } from "@/apis/login";
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
        dispatch(setToken(res.data.data.user_id))
    }
}

export {fetchLogin}

const userReducer = userStore.reducer
export default userReducer