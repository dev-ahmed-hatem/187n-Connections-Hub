import { Card, Space, Tag, Typography } from 'antd'
import { Table } from 'antd'

import { useAuditQuery } from '@/app/api/endpoints/access'
import type { AuditLog } from '@/types'

const { Title, Text } = Typography

const STATUS_COLOR: Record<string, string> = {
  ok: 'green',
  denied: 'red',
  error: 'volcano',
}

export default function AdminAuditPage() {
  const { data: logs } = useAuditQuery()

  const columns = [
    {
      title: 'When', dataIndex: 'created_at', key: 'created_at',
      render: (v: string) => new Date(v).toLocaleString(),
    },
    {
      title: 'Actor', key: 'actor',
      render: (_: unknown, a: AuditLog) => (
        <Space>
          <Tag>{a.actor_type}</Tag>
          <Text>{a.actor_label}</Text>
        </Space>
      ),
    },
    { title: 'Action', dataIndex: 'action', key: 'action' },
    { title: 'Client', dataIndex: 'client_org_name', key: 'client' },
    { title: 'Platform', dataIndex: 'provider_slug', key: 'provider' },
    {
      title: 'Result', key: 'status',
      render: (_: unknown, a: AuditLog) => (
        <Tag color={STATUS_COLOR[a.status] ?? 'default'}>{a.status}</Tag>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={3} style={{ marginBottom: 4 }}>Audit log</Title>
        <Text type="secondary">Every access-API call, including denied attempts.</Text>
      </div>
      <Card>
        <Table rowKey="id" dataSource={logs} columns={columns} pagination={{ pageSize: 15 }} />
      </Card>
    </Space>
  )
}
