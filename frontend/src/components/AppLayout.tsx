import type { ReactNode } from 'react'
import { Button, Layout, Menu, Tag, Typography } from 'antd'
import { useLocation, useNavigate } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/redux/hooks'
import { logout } from '@/app/slices/authSlice'
import { apiSlice } from '@/app/api/apiSlice'
import type { Role } from '@/types'

const { Header, Sider, Content } = Layout
const { Text } = Typography

const MENU: Record<Role, { key: string; label: string }[]> = {
  client: [
    { key: '/client/connections', label: 'Connections' },
    { key: '/client/updates', label: 'Updates & blockers' },
  ],
  developer: [
    { key: '/dev/access', label: 'Client access' },
    { key: '/dev/consumers', label: 'My API keys' },
  ],
  admin: [
    { key: '/admin/grants', label: 'Grants' },
    { key: '/admin/orgs', label: 'Clients & users' },
    { key: '/admin/announcements', label: 'Announcements' },
    { key: '/admin/audit', label: 'Audit log' },
  ],
}

const ROLE_COLOR: Record<Role, string> = {
  client: 'green',
  developer: 'geekblue',
  admin: 'purple',
}

export default function AppLayout({ children }: { children: ReactNode }) {
  const user = useAppSelector((s) => s.auth.user)
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const location = useLocation()

  if (!user) return null
  const items = MENU[user.role]

  const onLogout = () => {
    dispatch(logout())
    dispatch(apiSlice.util.resetApiState())
    navigate('/login')
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider breakpoint="lg" collapsedWidth="0" theme="light" width={230}
        style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: '20px 20px 12px', fontWeight: 700, fontSize: 16 }}>
          Connections Hub
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={items}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', borderBottom: '1px solid #f0f0f0',
          display: 'flex', alignItems: 'center', gap: 12, paddingInline: 20 }}>
          <Tag color={ROLE_COLOR[user.role]} style={{ textTransform: 'capitalize' }}>
            {user.role}
          </Tag>
          {user.client_org_name && <Text type="secondary">{user.client_org_name}</Text>}
          <div style={{ flex: 1 }} />
          <Text strong>{user.username}</Text>
          <Button onClick={onLogout}>Log out</Button>
        </Header>
        <Content style={{ padding: 24, maxWidth: 1080, width: '100%', margin: '0 auto' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}
