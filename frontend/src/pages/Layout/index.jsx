import React, { useState } from 'react';
import { HomeOutlined,EditOutlined,MenuOutlined } from '@ant-design/icons';
import { Menu } from 'antd';
import { Outlet } from 'react-router-dom';
import { getUserName } from '@/utils/userInfo';
const items = [
    {
    label:'Home',
    key: 'setting:1',
    icon: <HomeOutlined />,
    children: [
      {
        type: 'group',
        label: 'Item 1',
        children: [
          { label: 'Option 1', key: 'setting:1' },
          { label: 'Option 2', key: 'setting:2' },
        ],
      },
      {
        type: 'group',
        label: 'Item 2',
        children: [
          { label: 'Option 3', key: 'setting:3' },
          { label: 'Option 4', key: 'setting:4' },
        ],
      },
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
          { label: 'Option 1', key: 'setting:1' },
          { label: 'Option 2', key: 'setting:2' },
        ],
      },
      {
        type: 'group',
        label: 'Item 2',
        children: [
          { label: 'Option 3', key: 'setting:3' },
          { label: 'Option 4', key: 'setting:4' },
        ],
      },
    ],
  }
];
const Layout = () => {
  const [current, setCurrent] = useState('mail');
  const onClick = e => {
    console.log('click ', e);
    setCurrent(e.key);
  };
  return (
    <div>
      <Menu onClick={onClick} selectedKeys={[current]} mode="horizontal" items={items} />
      <Outlet/>
    </div>
  )
};
export default Layout;