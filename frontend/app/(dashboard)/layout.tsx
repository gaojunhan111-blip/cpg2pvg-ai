'use client'

import { ReactNode } from 'react'
import { Layout, Menu, Avatar, Dropdown, Button, Space } from 'antd'
import { UserOutlined, SettingOutlined, LogoutOutlined } from '@ant-design/icons'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const { Header, Sider, Content } = Layout

export default function DashboardLayout({
  children,
}: {
  children: ReactNode
}) {
  const pathname = usePathname()

  const menuItems = [
    {
      key: '/dashboard',
      label: <Link href="/dashboard">仪表板</Link>,
    },
    {
      key: '/dashboard/guidelines',
      label: <Link href="/dashboard/guidelines">指南管理</Link>,
    },
    {
      key: '/dashboard/upload',
      label: <Link href="/dashboard/upload">上传指南</Link>,
    },
    {
      key: '/dashboard/tasks',
      label: <Link href="/dashboard/tasks">任务监控</Link>,
    },
  ]

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      danger: true,
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={240} theme="light">
        <div className="p-4 border-b">
          <h1 className="text-lg font-bold text-blue-600">CPG2PVG-AI</h1>
          <p className="text-xs text-gray-500">临床指南转化系统</p>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[pathname]}
          items={menuItems}
          className="border-r"
        />
      </Sider>

      <Layout>
        <Header className="bg-white px-6 flex justify-between items-center border-b">
          <div className="text-lg font-semibold">
            临床指南转化系统
          </div>

          <Space>
            <Button type="text">帮助</Button>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button type="text" className="flex items-center">
                <Avatar size="small" icon={<UserOutlined />} />
                <span className="ml-2">用户</span>
              </Button>
            </Dropdown>
          </Space>
        </Header>

        <Content className="m-0">
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}