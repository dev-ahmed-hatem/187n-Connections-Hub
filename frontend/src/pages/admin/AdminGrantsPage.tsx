import {
  App,
  Button,
  Card,
  Form,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'

import {
  useConsumersQuery,
  useCreateGrantMutation,
  useDeleteGrantMutation,
  useGrantsQuery,
} from '@/app/api/endpoints/access'
import { useOrgsQuery, useProvidersQuery } from '@/app/api/endpoints/catalog'
import type { Grant } from '@/types'

const { Title, Text } = Typography

export default function AdminGrantsPage() {
  const { data: grants } = useGrantsQuery()
  const { data: consumers } = useConsumersQuery()
  const { data: orgs } = useOrgsQuery()
  const { data: providers } = useProvidersQuery()
  const [createGrant, { isLoading }] = useCreateGrantMutation()
  const [deleteGrant] = useDeleteGrantMutation()
  const { message, modal } = App.useApp()
  const [form] = Form.useForm()

  const onCreate = async (values: {
    consumer: number
    client_org: number
    provider: number
  }) => {
    try {
      await createGrant(values).unwrap()
      form.resetFields()
      message.success('Grant created.')
    } catch {
      message.error('Could not create the grant (maybe it already exists).')
    }
  }

  const columns = [
    { title: 'Project', dataIndex: 'consumer_name', key: 'consumer' },
    { title: 'Client', dataIndex: 'client_org_name', key: 'client' },
    { title: 'Platform', dataIndex: 'provider_name', key: 'provider' },
    {
      title: 'Active',
      key: 'active',
      render: (_: unknown, g: Grant) =>
        g.active ? <Tag color="green">yes</Tag> : <Tag>no</Tag>,
    },
    {
      title: '',
      key: 'actions',
      render: (_: unknown, g: Grant) => (
        <Button size="small" danger onClick={() =>
          modal.confirm({ title: 'Revoke this grant?', onOk: () => deleteGrant(g.id) })
        }>
          Revoke
        </Button>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={3} style={{ marginBottom: 4 }}>Grants</Title>
        <Text type="secondary">
          The access gate: a project can only reach a client/platform it has an active grant for.
        </Text>
      </div>

      <Card title="Grant access">
        <Form form={form} layout="inline" onFinish={onCreate}>
          <Form.Item name="consumer" rules={[{ required: true }]}>
            <Select placeholder="Project" style={{ minWidth: 180 }}
              options={(consumers ?? []).map((c) => ({ value: c.id, label: c.name }))} />
          </Form.Item>
          <Form.Item name="client_org" rules={[{ required: true }]}>
            <Select placeholder="Client" style={{ minWidth: 180 }}
              options={(orgs ?? []).map((o) => ({ value: o.id, label: o.name }))} />
          </Form.Item>
          <Form.Item name="provider" rules={[{ required: true }]}>
            <Select placeholder="Platform" style={{ minWidth: 160 }}
              options={(providers ?? []).map((p) => ({ value: p.id, label: p.name }))} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={isLoading}>Grant</Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="All grants">
        <Table rowKey="id" dataSource={grants} columns={columns} pagination={false} />
      </Card>
    </Space>
  )
}
