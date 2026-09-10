import { useState, type ReactNode } from 'react'
import { Button, Drawer, Dropdown, Grid, Layout, Menu, Tooltip } from 'antd'
import {
  ApiOutlined,
  BellOutlined,
  BulbFilled,
  BulbOutlined,
  CheckSquareOutlined,
  DashboardOutlined,
  FileTextOutlined,
  KeyOutlined,
  LinkOutlined,
  LogoutOutlined,
  MessageOutlined,
  MenuOutlined,
  DownOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useLocation, useNavigate } from 'react-router-dom'

import { useAppDispatch, useAppSelector } from '@/app/redux/hooks'
import { logout } from '@/app/slices/authSlice'
import { toggleTheme } from '@/app/slices/uiSlice'
import { apiSlice } from '@/app/api/apiSlice'
import NotificationsBell from '@/components/NotificationsBell'
import type { Role } from '@/types'

const { Header, Sider, Content } = Layout

const MENU: Record<Role, { key: string; label: string; icon: ReactNode }[]> = {
  client: [
    { key: '/', label: 'Dashboard', icon: <DashboardOutlined /> },
    { key: '/client/connections', label: 'Connections', icon: <LinkOutlined /> },
    { key: '/client/updates', label: 'Updates & blockers', icon: <BellOutlined /> },
  ],
  developer: [
    { key: '/', label: 'Dashboard', icon: <DashboardOutlined /> },
    { key: '/dev/projects', label: 'My projects', icon: <KeyOutlined /> },
    { key: '/staff/messages', label: 'Client messages', icon: <MessageOutlined /> },
    { key: '/dev/quickstart', label: 'Quickstart & API', icon: <ApiOutlined /> },
  ],
  admin: [
    { key: '/', label: 'Dashboard', icon: <DashboardOutlined /> },
    { key: '/admin/approvals', label: 'Approvals', icon: <CheckSquareOutlined /> },
    { key: '/admin/projects', label: 'Projects', icon: <SafetyCertificateOutlined /> },
    { key: '/admin/orgs', label: 'Clients & users', icon: <TeamOutlined /> },
    { key: '/staff/messages', label: 'Client messages', icon: <MessageOutlined /> },
    { key: '/admin/audit', label: 'Audit log', icon: <FileTextOutlined /> },
  ],
}

export default function AppLayout({ children }: { children: ReactNode }) {
  const user = useAppSelector((s) => s.auth.user)
  const dark = useAppSelector((s) => s.ui.dark)
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const location = useLocation()
  const screens = Grid.useBreakpoint()
  const [navigationOpen, setNavigationOpen] = useState(false)
  const mobile = !screens.lg

  if (!user) return null
  const items = MENU[user.role]
  const currentPage = items.find((item) => item.key === location.pathname)?.label ?? 'Account'
  const onLogout = () => {
    dispatch(logout())
    dispatch(apiSlice.util.resetApiState())
    navigate('/login')
  }
  const sidebar = (
    <div className="hub-sidebar-inner">
      <a className="hub-brand" href="/" onClick={(event) => { event.preventDefault(); navigate('/'); setNavigationOpen(false) }}>
        <img src="/187n-infinity.png" width="46" height="24" alt="" />
        <span className="hub-brand-name"><span className="hub-brand-title">187N</span><span className="hub-brand-sub">Connections Hub</span></span>
      </a>
      <p className="hub-eyebrow hub-nav-label">Workspace / {user.role}</p>
      <Menu mode="inline" className="hub-sidebar-menu" selectedKeys={[location.pathname]}
        items={items} onClick={({ key }) => { navigate(key); setNavigationOpen(false) }} />
      <div className="hub-workspace-card">
        <p className="hub-eyebrow">YOUR ORGANIZATION</p>
        <strong>{user.client_org_name || '187N Operations'}</strong>
        <small>One workspace. Connected teams.</small>
      </div>
      <div className="hub-sidebar-footer"><span>BUILT BY 187N</span><span>↗</span></div>
    </div>
  )

  return (
    <Layout className="hub-shell">
      <a className="hub-skip" href="#hub-main">Skip to content</a>
      {mobile ? (
        <Drawer className="hub-drawer" title="Navigation" placement="left" size={264}
          open={navigationOpen} onClose={() => setNavigationOpen(false)}>{sidebar}</Drawer>
      ) : <Sider width={244} className="hub-sidebar">{sidebar}</Sider>}
      <Layout>
        <Header className="hub-topbar">
          {mobile && <Button type="text" icon={<MenuOutlined />} aria-label="Open navigation"
            onClick={() => setNavigationOpen(true)} />}
          <div className="hub-breadcrumb"><span>Connections Hub</span><span className="hub-breadcrumb-divider">/</span><b>{currentPage}</b></div>
          <div className="hub-topbar-actions">
            <NotificationsBell />
            <Tooltip title={dark ? 'Light mode' : 'Dark mode'}>
              <Button type="text" aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
                icon={dark ? <BulbFilled /> : <BulbOutlined />} onClick={() => dispatch(toggleTheme())} />
            </Tooltip>
            <Dropdown trigger={['click']} menu={{ items: [
              { key: 'account', label: 'Account', icon: <UserOutlined /> },
              { type: 'divider' },
              { key: 'logout', label: 'Log out', icon: <LogoutOutlined />, danger: true },
            ], onClick: ({ key }) => (key === 'account' ? navigate('/account') : onLogout()) }}>
              <Button type="text" className="hub-user-button" aria-label="Your account menu">
                <span className="hub-avatar">{user.username.slice(0, 2).toUpperCase()}</span>
                <span className="hub-user-name">{user.username}</span><DownOutlined style={{ fontSize: 9 }} />
              </Button>
            </Dropdown>
          </div>
        </Header>
        <Content id="hub-main" className="hub-content" tabIndex={-1}>{children}</Content>
      </Layout>
    </Layout>
  )
}
