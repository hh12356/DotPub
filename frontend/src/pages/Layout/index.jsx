import React, { useEffect, useState } from 'react';
import { HomeOutlined,EditOutlined,MenuOutlined } from '@ant-design/icons';
import { Menu } from 'antd';
import { Outlet, useNavigate } from 'react-router-dom';
import { getUserName } from '@/utils/userName';

const Layout = () => {
  const [current, setCurrent] = useState('mail');
  const routeMap={
    hottest: '/home/hottest',
    latest: '/home/latest',
    greatest: '/home/greatest',
  }
  const navigate = useNavigate()
  const onClick = e => {
    // console.log('click ', e);
    setCurrent(e.key);
    navigate(routeMap[e.key])
  };

  //设置初始Home高亮
  useEffect(()=>{
    setCurrent('hottest')
  },[])

  //点击Home
  const onTitleClick = ()=>{
    setCurrent("hottest")
    navigate(routeMap['hottest'])
  }

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
            { label: 'Hottest', key: 'hottest' },
            { label: 'Latest', key: 'latest' },
            { label: 'Greatest', key: 'greatest' },
          ],
        }
      ],
    },
    {
      label: 'Write',
      key: 'write',
      icon: <EditOutlined />,
      // disabled: true,
    },
    {
      label: 'Search',
      key: 'search',
      icon: <MenuOutlined />,
      disabled: true,
    },
    {
      label: 'Notifications',
      key: 'notifications',
      icon: <MenuOutlined />,
      disabled: true,
    },
    {
      label: getUserName()||"未登录",
      key: 'profile',
      style: { marginLeft: 'auto', marginRight: 16 },
      children: [
        {
          type: 'group',
          label: 'Item 1',
          children: [
            { label: 'Option 1', key: 'setting:5' },
            { label: 'Option 2', key: 'setting:6' },
          ],
        },
      ],
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