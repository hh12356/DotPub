//路由配置
import Login from "../pages/Login"
import {createBrowserRouter} from 'react-router-dom'

//配置路由实例
const router = createBrowserRouter([
    {
        path:'/login',
        element:<Login/>
    }
])

export default router