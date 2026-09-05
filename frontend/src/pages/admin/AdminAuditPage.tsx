import { useState } from 'react'
import { Card, Select, Space, Table, Tag, Typography } from 'antd'

import { useAuditQuery } from '@/app/api/endpoints/access'
import type { AuditLog } from '@/types'

const { Title, Text } = Typography

const STATUS_COLOR: Record<string, string> = {
  ok: 'green',
  denied: 'red',
  error: 'volcano',
}

export default function AdminAuditPage() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(15)
  const [status, setStatus] = useState<string | undefined>()
  const { data, isFetching } = useAuditQuery({ page, page_size: pageSize, status })

  const columns = [
    {
      title: 'When', dataIndex: 'created_at', key: 'created_at',
      render: (v: string) => new Date(v).toLocaleString(),
    },
    {
      title: 'Actor', key: 'actor',
      render: (_: unknown, a: AuditLog) => (
        <Space><Tag>{a.actor_type}</Tag><Text>{a.actor_label}</Text></Space>
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
      <Space>
        <Select
          allowClear placeholder="Filter by result" style={{ minWidth: 180 }}
          value={status}
          onChange={(v) => { setStatus(v); setPage(1) }}
          options={[
            { value: 'ok', label: 'OK' },
            { value: 'denied', label: 'Denied' },
            { value: 'error', label: 'Error' },
          ]}
        />
      </Space>
      <Card>
        <Table
          rowKey="id"
          loading={isFetching}
          dataSource={data?.results}
          columns={columns}
          pagination={{
            current: page,
            pageSize,
            total: data?.count ?? 0,
            showSizeChanger: true,
            onChange: (p, ps) => { setPage(p); setPageSize(ps) },
          }}
        />
      </Card>
    </Space>
  )
}
