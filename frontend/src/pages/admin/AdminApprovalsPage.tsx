import { App, Button, Card, Empty, Segmented, Space, Table, Tag, Typography } from 'antd'
import { CheckOutlined, CloseOutlined } from '@ant-design/icons'
import { useState } from 'react'

import {
  useApproveGrantRequestMutation,
  useDenyGrantRequestMutation,
  useGrantRequestsQuery,
} from '@/app/api/endpoints/access'
import type { GrantRequest } from '@/types'

const { Title, Text } = Typography

const STATUS_COLOR: Record<string, string> = {
  pending: 'gold',
  approved: 'green',
  denied: 'red',
}

export default function AdminApprovalsPage() {
  const { data: requests, isLoading } = useGrantRequestsQuery()
  const [approve] = useApproveGrantRequestMutation()
  const [deny] = useDenyGrantRequestMutation()
  const { message } = App.useApp()
  const [filter, setFilter] = useState<'pending' | 'all'>('pending')

  const rows = (requests ?? []).filter((r) => filter === 'all' || r.status === 'pending')

  const columns = [
    { title: 'Project', dataIndex: 'consumer_name', key: 'consumer' },
    { title: 'Client', dataIndex: 'client_org_name', key: 'client' },
    { title: 'Platform', dataIndex: 'provider_name', key: 'provider' },
    {
      title: 'Scopes', key: 'scopes',
      render: (_: unknown, r: GrantRequest) =>
        (r.scopes?.length ? r.scopes : ['(all)']).map((s) => <Tag key={s}>{s}</Tag>),
    },
    { title: 'Requested by', dataIndex: 'requested_by_username', key: 'by' },
    {
      title: 'Status', key: 'status',
      render: (_: unknown, r: GrantRequest) => <Tag color={STATUS_COLOR[r.status]}>{r.status}</Tag>,
    },
    {
      title: 'Actions', key: 'actions',
      render: (_: unknown, r: GrantRequest) =>
        r.status === 'pending' ? (
          <Space>
            <Button size="small" type="primary" icon={<CheckOutlined />}
              onClick={async () => { await approve(r.id).unwrap(); message.success('Approved — grant created.') }}>
              Approve
            </Button>
            <Button size="small" danger icon={<CloseOutlined />}
              onClick={async () => { await deny(r.id).unwrap(); message.info('Request denied.') }}>
              Deny
            </Button>
          </Space>
        ) : (
          <Text type="secondary">decided</Text>
        ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={3} style={{ marginBottom: 4 }}>Access approvals</Title>
        <Text type="secondary">
          Approving a request creates the grant that lets the project reach that client/platform.
        </Text>
      </div>
      <Segmented value={filter} onChange={(v) => setFilter(v as 'pending' | 'all')}
        options={[{ label: 'Pending', value: 'pending' }, { label: 'All', value: 'all' }]} />
      <Card>
        <Table rowKey="id" loading={isLoading} dataSource={rows} columns={columns}
          pagination={false}
          locale={{ emptyText: <Empty description="Nothing to approve" /> }} />
      </Card>
    </Space>
  )
}
