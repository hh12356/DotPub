import React, { useEffect, useState } from 'react';
import {
  HomeOutlined, EditOutlined, MenuOutlined, SearchOutlined,
  FireOutlined, ClockCircleOutlined, TrophyOutlined,
  UserOutlined, LogoutOutlined,
  HeartOutlined,
  StarOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { Menu } from 'antd';
import { Outlet, useNavigate } from 'react-router-dom';
import { getUserName, removeUserName } from '@/utils/userName';
import './index.scss';
import { removeToken, getUserId } from '@/utils/token';

const Layout = () => {
  const [current, setCurrent] = useState('mail');
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
    article:'/userart'
  }
  const navigate = useNavigate()
  const onClick = e => {
    // console.log('click ', e);
    setCurrent(e.key);
    //逻辑
    if(e.key==='exit'){
      removeToken()
      removeUserName()
    }
    navigate(routeMap[e.key])
  };

  //设置初始Home高亮
  useEffect(()=>{
    setCurrent('hottest')
  },[])

  //点击Home
  const onTitleClick = ()=>{
    setCurrent("hottest")
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
      label: 'Notifications',
      key: 'notifications',
      icon: <MenuOutlined />,
      disabled: true,
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
    </div>
  )
};
export default Layout;