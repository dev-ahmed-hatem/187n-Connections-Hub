import type { ReactNode } from 'react'
import { Button, Layout, Menu, Tag, Tooltip, Typography, theme } from 'antd'
import {
  ApiOutlined,
  AppstoreOutlined,
  BellOutlined,
  BulbFilled,
  BulbOutlined,
  CheckSquareOutlined,
  DashboardOutlined,
  FileTextOutlined,
  KeyOutlined,
  LinkOutlined,
  LogoutOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/redux/hooks'
import { logout } from '@/app/slices/authSlice'
import { toggleTheme } from '@/app/slices/uiSlice'
import { apiSlice } from '@/app/api/apiSlice'
import type { Role } from '@/types'

const { Header, Sider, Content } = Layout
const { Text } = Typography

const MENU: Record<Role, { key: string; label: string; icon: ReactNode }[]> = {
  client: [
    { key: '/', label: 'Dashboard', icon: <DashboardOutlined /> },
    { key: '/client/connections', label: 'Connections', icon: <LinkOutlined /> },
    { key: '/client/updates', label: 'Updates & blockers', icon: <BellOutlined /> },
  ],
  developer: [
    { key: '/', label: 'Dashboard', icon: <DashboardOutlined /> },
    { key: '/dev/access', label: 'Client access', icon: <AppstoreOutlined /> },
    { key: '/dev/projects', label: 'My projects', icon: <KeyOutlined /> },
    { key: '/dev/quickstart', label: 'Quickstart & API', icon: <ApiOutlined /> },
  ],
  admin: [
    { key: '/', label: 'Dashboard', icon: <DashboardOutlined /> },
    { key: '/admin/approvals', label: 'Approvals', icon: <CheckSquareOutlined /> },
    { key: '/admin/grants', label: 'Grants', icon: <SafetyCertificateOutlined /> },
    { key: '/admin/orgs', label: 'Clients & users', icon: <TeamOutlined /> },
    { key: '/admin/announcements', label: 'Announcements', icon: <BellOutlined /> },
    { key: '/admin/audit', label: 'Audit log', icon: <FileTextOutlined /> },
  ],
}

const ROLE_COLOR: Record<Role, string> = {
  client: 'green',
  developer: 'geekblue',
  admin: 'purple',
}

export default function AppLayout({ children }: { children: ReactNode }) {
  const user = useAppSelector((s) => s.auth.user)
  const dark = useAppSelector((s) => s.ui.dark)
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const location = useLocation()
  const { token } = theme.useToken()

  if (!user) return null
  const items = MENU[user.role]

  const onLogout = () => {
    dispatch(logout())
    dispatch(apiSlice.util.resetApiState())
    navigate('/login')
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider breakpoint="lg" collapsedWidth="0" width={230}
        style={{ background: token.colorBgContainer, borderRight: `1px solid ${token.colorBorderSecondary}` }}>
        <div style={{ padding: '20px 20px 12px', fontWeight: 700, fontSize: 16,
          color: token.colorText }}>
          Connections Hub
        </div>
        <Menu
          mode="inline"
          style={{ background: 'transparent', borderInlineEnd: 'none' }}
          selectedKeys={[location.pathname]}
          items={items}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: token.colorBgContainer,
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          display: 'flex', alignItems: 'center', gap: 12, paddingInline: 20 }}>
          <Tag color={ROLE_COLOR[user.role]} style={{ textTransform: 'capitalize' }}>
            {user.role}
          </Tag>
          {user.client_org_name && <Text type="secondary">{user.client_org_name}</Text>}
          <div style={{ flex: 1 }} />
          <Text strong>{user.username}</Text>
          <Tooltip title={dark ? 'Light mode' : 'Dark mode'}>
            <Button
              type="text"
              aria-label="Toggle theme"
              icon={dark ? <BulbFilled /> : <BulbOutlined />}
              onClick={() => dispatch(toggleTheme())}
            />
          </Tooltip>
          <Button icon={<LogoutOutlined />} onClick={onLogout}>Log out</Button>
        </Header>
        <Content style={{ padding: 24, maxWidth: 1080, width: '100%', margin: '0 auto' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}
