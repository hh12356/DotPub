//路由配置
import Layout from "@/pages/Layout"
import Login from "../pages/Login"
import Signup from "../pages/Signup"
import Write from "@/pages/Write"
import Home from '@/pages/Home'
import {createBrowserRouter} from 'react-router-dom'
import Article from "@/pages/Article"
import Search from "@/pages/Search"
import Likes from "@/pages/User/Likes"
import Stars from "@/pages/User/Stars"
import Profile from "@/pages/User/Profile"
import UserArt from "@/pages/User/UserArt"

//配置路由实例
const router = createBrowserRouter([
    {
        path:'/',
        element:<Layout/>,
        children:[
            {
                path:'/',
                element:<Home sort="hot"/>
            },
            {
                path:'/home/hottest',
                element:<Home sort="hot"/>
            },
            {
                path:'/home/latest',
                element:<Home sort="latest"/>
            },
            {
                path:'/home/greatest',
                element:<Home sort="greatest"/>
            },
            {
                path:'/write',
                element:<Write/>
            },
            {
                path:'/write/:id',
                element:<Write/>
            },
            {
                //使用useParams读取id，拿到的永远是字符串，用Number()转换
                path:'/article/:id',
                element:<Article/>
            },
            {
                path:'/search',
                element:<Search/>
            },
            {
                path:'/likes',
                element:<Likes/>
            },
            {
                path:'/stars',
                element:<Stars/>
            },
            {
                path:'/profile/:id',
                element:<Profile/>
            },
            {
                path:'/userart',
                element:<UserArt/>
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