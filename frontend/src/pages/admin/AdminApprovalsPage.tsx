import { App, Button, Card, Empty, Segmented, Space, Table, Tag, Typography } from 'antd'
import { CheckOutlined, CloseOutlined } from '@ant-design/icons'
import { useState } from 'react'

import {
  useApproveProjectRequestMutation,
  useDenyProjectRequestMutation,
  useProjectRequestsQuery,
} from '@/app/api/endpoints/access'
import type { ProjectAccessRequest } from '@/types'

const { Title, Text } = Typography

const STATUS_COLOR: Record<string, string> = {
  pending: 'gold', approved: 'green', denied: 'red',
}

export default function AdminApprovalsPage() {
  const { data: requests, isLoading } = useProjectRequestsQuery()
  const [approve] = useApproveProjectRequestMutation()
  const [deny] = useDenyProjectRequestMutation()
  const { message } = App.useApp()
  const [filter, setFilter] = useState<'pending' | 'all'>('pending')

  const rows = (requests ?? []).filter((r) => filter === 'all' || r.status === 'pending')

  const columns = [
    { title: 'Project', dataIndex: 'consumer_name', key: 'project' },
    { title: 'Client', dataIndex: 'client_org_name', key: 'client' },
    { title: 'Requested by', dataIndex: 'requested_by_username', key: 'by' },
    { title: 'Message', dataIndex: 'message', key: 'message' },
    { title: 'Status', key: 'status',
      render: (_: unknown, r: ProjectAccessRequest) => <Tag color={STATUS_COLOR[r.status]}>{r.status}</Tag> },
    {
      title: 'Actions', key: 'actions',
      render: (_: unknown, r: ProjectAccessRequest) =>
        r.status === 'pending' ? (
          <Space>
            <Button size="small" type="primary" icon={<CheckOutlined />}
              onClick={async () => { await approve(r.id).unwrap(); message.success('Approved — developer added.') }}>
              Approve
            </Button>
            <Button size="small" danger icon={<CloseOutlined />}
              onClick={async () => { await deny(r.id).unwrap(); message.info('Denied.') }}>
              Deny
            </Button>
          </Space>
        ) : <Text type="secondary">decided</Text>,
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={3} style={{ marginBottom: 4 }}>Access approvals</Title>
        <Text type="secondary">Approving adds the developer to the project's members.</Text>
      </div>
      <Segmented value={filter} onChange={(v) => setFilter(v as 'pending' | 'all')}
        options={[{ label: 'Pending', value: 'pending' }, { label: 'All', value: 'all' }]} />
      <Card>
        <Table rowKey="id" loading={isLoading} dataSource={rows} columns={columns}
          pagination={false} locale={{ emptyText: <Empty description="Nothing to approve" /> }} />
      </Card>
    </Space>
  )
}
