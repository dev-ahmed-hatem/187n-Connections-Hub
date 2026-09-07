import { Card, Col, Empty, Row, Space, Spin, Statistic, Tag, Typography } from 'antd'
import { Link } from 'react-router-dom'

import { useDashboardQuery } from '@/app/api/endpoints/dashboard'
import { useAppSelector } from '@/app/redux/hooks'

const { Title, Text } = Typography

function StatCard({ label, value, to }: { label: string; value: number; to?: string }) {
  const body = <Card><Statistic title={label} value={value} /></Card>
  return to ? <Link to={to}>{body}</Link> : body
}

const STATUS_COLOR: Record<string, string> = {
  connected: 'green',
  needs_reconnect: 'gold',
  disconnected: 'default',
  error: 'red',
}

export default function DashboardPage() {
  const user = useAppSelector((s) => s.auth.user)
  const { data, isLoading } = useDashboardQuery()

  if (isLoading || !data) return <Spin />
  const d = data as Record<string, number | string | object>

  const statusChips = (obj: Record<string, number>) =>
    Object.keys(obj || {}).length ? (
      <Space wrap>
        {Object.entries(obj).map(([k, v]) => (
          <Tag key={k} color={STATUS_COLOR[k] ?? 'default'}>
            {k.replace('_', ' ')}: {v}
          </Tag>
        ))}
      </Space>
    ) : (
      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No connections yet" />
    )

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={3} style={{ marginBottom: 4 }}>
          Welcome, {user?.username}
        </Title>
        <Text type="secondary">Here's your hub at a glance.</Text>
      </div>

      {data.role === 'admin' && (
        <>
          <Row gutter={[16, 16]}>
            <Col xs={12} md={6}><StatCard label="Clients" value={d.clients as number} to="/admin/orgs" /></Col>
            <Col xs={12} md={6}><StatCard label="Projects" value={d.projects as number} to="/admin/projects" /></Col>
            <Col xs={12} md={6}><StatCard label="Pending requests" value={d.pending_requests as number} to="/admin/approvals" /></Col>
            <Col xs={12} md={6}><StatCard label="Live providers" value={d.providers_live as number} /></Col>
          </Row>
          <Card title="Connections by status">
            {statusChips(d.connections_by_status as Record<string, number>)}
          </Card>
          <Card title="Recent activity">
            {(d.recent_audit as { actor: string; action: string; status: string; provider: string; created_at: string }[])?.length ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                {(d.recent_audit as { actor: string; action: string; status: string; provider: string; created_at: string }[]).map((a, i) => (
                  <Text key={i}>
                    <Tag color={a.status === 'ok' ? 'green' : a.status === 'denied' ? 'red' : 'volcano'}>{a.status}</Tag>
                    <b>{a.actor}</b> — {a.action}{a.provider ? ` · ${a.provider}` : ''}
                  </Text>
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
          <Card title="Your connections">
            {statusChips(d.connections_by_status as Record<string, number>)}
          </Card>
        </>
      )}
    </Space>
  )
}
