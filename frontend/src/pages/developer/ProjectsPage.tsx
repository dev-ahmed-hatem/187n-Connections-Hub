import { useState } from 'react'
import {
  App,
  Button,
  Card,
  Checkbox,
  Drawer,
  Empty,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'
import { KeyOutlined, PlusOutlined, ReloadOutlined, SafetyOutlined } from '@ant-design/icons'

import {
  useConsumerAccessQuery,
  useConsumersQuery,
  useCreateConsumerMutation,
  useCreateGrantRequestMutation,
  useGrantRequestsQuery,
  useRotateKeyMutation,
} from '@/app/api/endpoints/access'
import { useOrgsQuery, useProvidersQuery } from '@/app/api/endpoints/catalog'
import type { Consumer } from '@/types'

const { Title, Text, Paragraph } = Typography

const STATUS_COLOR: Record<string, string> = {
  connected: 'green',
  needs_reconnect: 'gold',
  not_connected: 'default',
}

export default function ProjectsPage() {
  const { data: consumers, isLoading } = useConsumersQuery()
  const { data: requests } = useGrantRequestsQuery()
  const { data: orgs } = useOrgsQuery()
  const { data: providers } = useProvidersQuery()
  const [createConsumer, { isLoading: creating }] = useCreateConsumerMutation()
  const [rotateKey] = useRotateKeyMutation()
  const [createRequest, { isLoading: requesting }] = useCreateGrantRequestMutation()
  const { message, modal } = App.useApp()

  const [createForm] = Form.useForm()
  const [requestForm] = Form.useForm()
  const [createOpen, setCreateOpen] = useState(false)
  const [requestOpen, setRequestOpen] = useState(false)
  const [accessFor, setAccessFor] = useState<Consumer | null>(null)

  const showKey = (title: string, key: string) =>
    modal.success({
      title,
      content: (
        <div>
          <Paragraph>Copy this key now — it is shown only once:</Paragraph>
          <Paragraph copyable code style={{ wordBreak: 'break-all' }}>{key}</Paragraph>
        </div>
      ),
    })

  const onCreate = async (v: { name: string }) => {
    try {
      const c = await createConsumer(v).unwrap()
      setCreateOpen(false); createForm.resetFields()
      showKey('API key created', c.api_key!)
    } catch { message.error('Could not create the project.') }
  }

  const onRotate = (c: Consumer) =>
    modal.confirm({
      title: `Rotate key for "${c.name}"?`,
      content: 'The current key stops working immediately.',
      onOk: async () => {
        const updated = await rotateKey(c.id).unwrap()
        showKey('New API key', updated.api_key!)
      },
    })

  const onRequest = async (v: { consumer: number; client_org: number; provider: number; scopes: string[]; message?: string }) => {
    try {
      await createRequest(v).unwrap()
      setRequestOpen(false); requestForm.resetFields()
      message.success('Access request sent for approval.')
    } catch { message.error('Could not send the request (it may already exist).') }
  }

  const columns = [
    { title: 'Project', dataIndex: 'name', key: 'name' },
    { title: 'Key', key: 'key', render: (_: unknown, c: Consumer) => <Text code>{c.api_key_prefix}…</Text> },
    {
      title: 'Status', key: 'active',
      render: (_: unknown, c: Consumer) => c.active ? <Tag color="green">active</Tag> : <Tag>inactive</Tag>,
    },
    {
      title: 'Actions', key: 'actions',
      render: (_: unknown, c: Consumer) => (
        <Space>
          <Button size="small" icon={<SafetyOutlined />} onClick={() => setAccessFor(c)}>Access</Button>
          <Button size="small" icon={<ReloadOutlined />} onClick={() => onRotate(c)}>Rotate key</Button>
        </Space>
      ),
    },
  ]

  const pending = (requests ?? []).filter((r) => r.status === 'pending')

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <Title level={3} style={{ marginBottom: 4 }}>My projects</Title>
          <Text type="secondary">
            Each project has its own API key and reaches only the clients an admin has approved.
          </Text>
        </div>
        <Space>
          <Button icon={<KeyOutlined />} onClick={() => setRequestOpen(true)}>Request access</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>New project</Button>
        </Space>
      </div>

      <Card title="Projects">
        <Table rowKey="id" loading={isLoading} dataSource={consumers} columns={columns}
          pagination={false}
          locale={{ emptyText: <Empty description="No projects yet — create one to get an API key" /> }} />
      </Card>

      <Card title="My access requests">
        {pending.length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No pending requests" />
        ) : (
          <Space direction="vertical" style={{ width: '100%' }}>
            {pending.map((r) => (
              <Text key={r.id}>
                <Tag color="gold">pending</Tag>
                <b>{r.consumer_name}</b> → {r.client_org_name} · {r.provider_name}
              </Text>
            ))}
          </Space>
        )}
      </Card>

      {/* Access drill-down */}
      <Drawer title={accessFor ? `Access · ${accessFor.name}` : ''} open={!!accessFor}
        onClose={() => setAccessFor(null)} width={480}>
        {accessFor && <AccessList consumerId={accessFor.id} />}
      </Drawer>

      {/* Create project */}
      <Modal title="New project" open={createOpen} onCancel={() => setCreateOpen(false)}
        onOk={() => createForm.submit()} confirmLoading={creating} okText="Create">
        <Form form={createForm} layout="vertical" onFinish={onCreate}>
          <Form.Item name="name" label="Project name" rules={[{ required: true }]}>
            <Input placeholder="e.g. shopify-operator" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Request access */}
      <Modal title="Request access" open={requestOpen} onCancel={() => setRequestOpen(false)}
        onOk={() => requestForm.submit()} confirmLoading={requesting} okText="Send request">
        <Form form={requestForm} layout="vertical" onFinish={onRequest}
          initialValues={{ scopes: ['read', 'token'] }}>
          <Form.Item name="consumer" label="Project" rules={[{ required: true }]}>
            <Select options={(consumers ?? []).map((c) => ({ value: c.id, label: c.name }))} />
          </Form.Item>
          <Form.Item name="client_org" label="Client" rules={[{ required: true }]}>
            <Select options={(orgs ?? []).map((o) => ({ value: o.id, label: o.name }))} />
          </Form.Item>
          <Form.Item name="provider" label="Platform" rules={[{ required: true }]}>
            <Select options={(providers ?? []).map((p) => ({ value: p.id, label: p.name }))} />
          </Form.Item>
          <Form.Item name="scopes" label="Scopes">
            <Checkbox.Group options={[
              { label: 'Read data', value: 'read' },
              { label: 'Fetch token', value: 'token' },
            ]} />
          </Form.Item>
          <Form.Item name="message" label="Message (optional)">
            <Input.TextArea rows={2} placeholder="Why you need access" />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  )
}

function AccessList({ consumerId }: { consumerId: number }) {
  const { data, isLoading } = useConsumerAccessQuery(consumerId)
  if (isLoading) return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Loading…" />
  if (!data?.access.length)
    return <Empty description="No access yet — request access to a client/platform" />
  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      {data.access.map((a) => (
        <Card key={a.grant_id} size="small">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 600 }}>{a.client_org_name}</div>
              <Text type="secondary">
                {a.provider_name}{a.external_account_id ? ` · ${a.external_account_id}` : ''}
              </Text>
            </div>
            <Tag color={STATUS_COLOR[a.connection_status] ?? 'default'}>
              {a.connection_status.replace('_', ' ')}
            </Tag>
          </div>
        </Card>
      ))}
    </Space>
  )
}
