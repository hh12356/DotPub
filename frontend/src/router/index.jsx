//路由配置
import Layout from "@/pages/Layout"
import Login from "../pages/Login"
import Signup from "../pages/Signup"
import {createBrowserRouter} from 'react-router-dom'

//配置路由实例
const router = createBrowserRouter([
    {
        path:'/',
        element:<Layout/>
    },
    {
        path:'/login',
        element:<Login/>
    },
    {
        path:'/signup',
        element:<Signup/>
    },
])

export default router