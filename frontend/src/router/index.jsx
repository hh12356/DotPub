//路由配置
import Layout from "@/pages/Layout"
import Login from "../pages/Login"
import Signup from "../pages/Signup"
import Write from "@/pages/Write"
import { Greatest,Latest,Hottest } from '@/pages/Home'
import {createBrowserRouter} from 'react-router-dom'

//配置路由实例
const router = createBrowserRouter([
    {
        path:'/',
        element:<Layout/>,
        children:[
            {
                path:'/',
                element:<Hottest/>
            },
            {
                path:'/home/hottest',
                element:<Hottest/>
            },
            {
                path:'/home/latest',
                element:<Latest/>
            },
            {
                path:'/home/greatest',
                element:<Greatest/>
            },
            {
                path:'/write',
                element:<Write/>
            },
        ]
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