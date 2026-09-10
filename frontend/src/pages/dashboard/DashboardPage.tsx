import { Alert, Button, Card, Col, Empty, Row, Space, Spin, Statistic, Tag, Typography } from 'antd'
import { ArrowRightOutlined, ArrowUpOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'

import { useDashboardQuery } from '@/app/api/endpoints/dashboard'
import { useAppSelector } from '@/app/redux/hooks'

const { Text } = Typography

function StatCard({ label, value, to }: { label: string; value: number; to?: string }) {
  const body = <Card className="hub-stat-card"><div className="hub-stat-index"><span>WORKSPACE METRIC</span>{to && <ArrowUpOutlined rotate={45} />}</div><Statistic title={label} value={value} /></Card>
  return to ? <Link to={to}>{body}</Link> : body
}

const STATUS_COLOR: Record<string, string> = {
  connected: 'blue',
  needs_reconnect: 'gold',
  disconnected: 'default',
  error: 'red',
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const user = useAppSelector((s) => s.auth.user)
  const { data, isLoading, error, refetch } = useDashboardQuery()

  if (isLoading) return <Spin />
  if (error || !data) return <Alert type="error" showIcon title="Your overview could not be loaded."
    action={<Button onClick={() => refetch()}>Try again</Button>} />
  const d = data as Record<string, number | string | object>

  const statusChips = (obj: Record<string, number>) =>
    Object.keys(obj || {}).length ? (
      <Space wrap>
        {Object.entries(obj).map(([k, v]) => (
          <Tag key={k} color={STATUS_COLOR[k] ?? 'default'}>
            {k === 'connected' ? 'Authorized' : k.replaceAll('_', ' ')}: {v}
          </Tag>
        ))}
      </Space>
    ) : (
      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No connections yet" />
    )

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div className="hub-page-intro">
        <div>
          <span className="hub-section-number">01 / WORKSPACE OVERVIEW</span>
          <h1>Your connected<br /><em>operation.</em></h1>
          <p>Welcome back, {user?.first_name || user?.username}. Your accounts, projects and next steps, all in one place.</p>
        </div>
        <Button onClick={() => navigate(data.role === 'admin' ? '/admin/orgs' : data.role === 'developer' ? '/dev/projects' : '/client/connections')}
          type="primary" icon={<ArrowRightOutlined />} iconPlacement="end">
            {data.role === 'admin' ? 'Manage clients' : data.role === 'developer' ? 'View projects' : 'Manage connections'}
        </Button>
      </div>

      {data.role === 'admin' && (
        <>
          <Row gutter={[16, 16]}>
            <Col xs={12} md={6}><StatCard label="Clients" value={d.clients as number} to="/admin/orgs" /></Col>
            <Col xs={12} md={6}><StatCard label="Projects" value={d.projects as number} to="/admin/projects" /></Col>
            <Col xs={12} md={6}><StatCard label="Pending requests" value={d.pending_requests as number} to="/admin/approvals" /></Col>
            <Col xs={12} md={6}><StatCard label="Live providers" value={d.providers_live as number} /></Col>
          </Row>
          <Card title="Connection authorizations">
            {statusChips(d.connections_by_status as Record<string, number>)}
          </Card>
          <Card title="Recent activity">
            {(d.recent_audit as { actor: string; action: string; status: string; provider: string; created_at: string }[])?.length ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                {(d.recent_audit as { actor: string; action: string; status: string; provider: string; created_at: string }[]).map((a, i) => (
                  <div className="hub-activity-row" key={i}>
                    <Tag color={a.status === 'ok' ? 'green' : a.status === 'denied' ? 'red' : 'volcano'}>{a.status}</Tag>
                    <Text><b>{a.actor}</b> · {a.action}{a.provider ? ` / ${a.provider}` : ''}</Text>
                    <small>{new Date(a.created_at).toLocaleDateString()}</small>
                  </div>
                ))}
              </Space>
            ) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No activity yet" />}
          </Card>
        </>
      )}

      {data.role === 'developer' && (
        <Row gutter={[16, 16]}>
          <Col xs={12} md={8}><StatCard label="My projects" value={d.my_projects as number} to="/dev/projects" /></Col>
          <Col xs={12} md={8}><StatCard label="Pending requests" value={d.my_pending_requests as number} to="/dev/projects" /></Col>
        </Row>
      )}

      {data.role === 'client' && (
        <>
          <Row gutter={[16, 16]}>
            <Col xs={12} md={8}><StatCard label="Platforms available" value={d.total_providers as number} to="/client/connections" /></Col>
            <Col xs={12} md={8}><StatCard label="Open blockers" value={d.open_blockers as number} to="/client/updates" /></Col>
            <Col xs={12} md={8}><StatCard label="Pending requests" value={d.pending_requests as number} to="/client/updates" /></Col>
          </Row>
          <Card title="Your connection authorizations">
            {statusChips(d.connections_by_status as Record<string, number>)}
          </Card>
        </>
      )}
    </Space>
  )
}
