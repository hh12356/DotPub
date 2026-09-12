//路由配置
import Layout from "@/pages/Layout"
import Login from "../pages/Login"
import Signup from "../pages/Signup"
import Write from "@/pages/Write"
import { Greatest,Latest,Hottest } from '@/pages/Home'
import {createBrowserRouter} from 'react-router-dom'
import Article from "@/pages/Article"

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
            {
                //使用useParams读取id，拿到的永远是字符串，用Number()转换
                path:'/article/:id',
                element:<Article/>
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