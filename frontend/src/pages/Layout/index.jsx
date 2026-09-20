import React from 'react';
import {
  HomeOutlined, EditOutlined, MenuOutlined, SearchOutlined,
  FireOutlined, ClockCircleOutlined, TrophyOutlined,
  UserOutlined, LogoutOutlined,
  HeartOutlined,
  StarOutlined,
  FileTextOutlined,
  DashboardOutlined,
} from '@ant-design/icons';
import { Menu } from 'antd';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { getUserName, removeUserName } from '@/utils/userName';
import { getUserRole, removeUserRole } from '@/utils/userRole';
import './index.scss';
import { removeToken, getUserId } from '@/utils/token';
import ChatFloat from '@/components/ChatFloat';

//路径 → 该亮哪一项
const PATH_KEY = {
  '/':'hottest',
  '/home/hottest':'hottest',
  '/home/latest':'latest',
  '/home/greatest':'greatest',
  '/write':'write',
  '/search':'search',
  '/likes':'likes',
  '/stars':'stars',
  '/userart':'article',
  '/admin':'admin',
}

const Layout = () => {
  const routeMap={
    hottest: '/home/hottest',
    latest: '/home/latest',
    greatest: '/home/greatest',
    write:'/write',
    login:'/login',
    profile:`/profile/${getUserId()}`,
    exit:'/',
    search:'/search',
    likes:'/likes',
    stars:'/stars',
    article:'/userart',
    admin:'/admin'
  }
  const navigate = useNavigate()

  //高亮不用 state 存，从 URL 现推——刷新、前进后退、直接粘地址进来都不会错
  const { pathname } = useLocation()

  //当前文章id，没有就是 null（首页、搜索页等）
  const artId = Number(pathname.match(/^\/article\/(\d+)/)?.[1]) || null

  const current = PATH_KEY[pathname]
    ?? (pathname.startsWith('/profile') ? 'profile'
    :   pathname.startsWith('/write')   ? 'write'
    :   undefined)

  const onClick = e => {
    //逻辑
    if(e.key==='exit'){
      removeToken()
      removeUserName()
      removeUserRole()
    }
    navigate(routeMap[e.key])
  };

  //点击Home
  const onTitleClick = ()=>{
    navigate('/')
  }

  const userName = getUserName()

  const items = [
    {
      label:'Home',
      key: 'home',
      icon: <HomeOutlined />,
      onTitleClick:onTitleClick,
      children: [
        {
          type: 'group',
          label: 'Explore',
          children: [
            { label: 'Hottest', key: 'hottest', icon: <FireOutlined /> },
            { label: 'Latest', key: 'latest', icon: <ClockCircleOutlined /> },
            { label: 'Greatest', key: 'greatest', icon: <TrophyOutlined /> },
          ],
        }
      ],
    },
    {
      label: 'Write',
      key: 'write',
      icon: <EditOutlined />
      // disabled: true,
    },
    {
      label: 'Search',
      key: 'search',
      icon: <SearchOutlined />,
    },
    {
      label: userName||"登录",
      key: 'login',
      style: { marginLeft: 'auto', marginRight: 16 },
      ...(userName&&{
        children: [
          {
            type: 'group',
            label: 'User',
            children: [
              { label: 'Profile', key: 'profile', icon: <UserOutlined /> },
              { label: 'Article', key: 'article', icon: <FileTextOutlined /> },
              { label: 'Likes', key: 'likes', icon: <HeartOutlined /> },
              { label: 'Stars', key: 'stars', icon: <StarOutlined /> },
              ...(getUserRole()==='admin'
                ? [{ label: 'Admin', key: 'admin', icon: <DashboardOutlined /> }]
                : []),
              { label: 'Exit', key: 'exit', icon: <LogoutOutlined /> },
            ],
          },
        ],
      })
    }
  ];

  return (
    <div>
      <Menu onClick={onClick} selectedKeys={[current]} mode="horizontal" items={items} />
      <Outlet/>
      {/* 换用户或换文章都重挂：对话是按 用户+文章 存的，重挂才会去读对应的那一份 */}
      <ChatFloat key={`${getUserId()}_${artId}`} artId={artId}/>
    </div>
  )
};
export default Layout;