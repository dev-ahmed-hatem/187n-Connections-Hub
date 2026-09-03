import { useState } from 'react'
import {
  App,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'

import {
  useConsumersQuery,
  useCreateConsumerMutation,
  useDeleteConsumerMutation,
  useGrantsQuery,
} from '@/app/api/endpoints/access'
import type { Consumer, Grant } from '@/types'

const { Title, Text, Paragraph } = Typography

export default function DevConsumersPage() {
  const { data: consumers } = useConsumersQuery()
  const { data: grants } = useGrantsQuery()
  const [createConsumer, { isLoading }] = useCreateConsumerMutation()
  const [deleteConsumer] = useDeleteConsumerMutation()
  const { message, modal } = App.useApp()
  const [form] = Form.useForm()
  const [open, setOpen] = useState(false)

  const onCreate = async (values: { name: string }) => {
    try {
      const consumer = await createConsumer(values).unwrap()
      setOpen(false)
      form.resetFields()
      modal.success({
        title: 'API key created',
        content: (
          <div>
            <Paragraph>Copy this key now — it is shown only once:</Paragraph>
            <Paragraph copyable code style={{ wordBreak: 'break-all' }}>
              {consumer.api_key}
            </Paragraph>
          </div>
        ),
      })
    } catch {
      message.error('Could not create the API key.')
    }
  }

  const consumerColumns = [
    { title: 'Project', dataIndex: 'name', key: 'name' },
    {
      title: 'Key',
      key: 'key',
      render: (_: unknown, c: Consumer) => <Text code>{c.api_key_prefix}…</Text>,
    },
    {
      title: 'Status',
      key: 'active',
      render: (_: unknown, c: Consumer) =>
        c.active ? <Tag color="green">active</Tag> : <Tag>inactive</Tag>,
    },
    {
      title: '',
      key: 'actions',
      render: (_: unknown, c: Consumer) => (
        <Button
          size="small"
          danger
          onClick={() =>
            modal.confirm({
              title: `Delete "${c.name}"?`,
              content: 'Projects using this key will lose access.',
              onOk: () => deleteConsumer(c.id),
            })
          }
        >
          Delete
        </Button>
      ),
    },
  ]

  const grantColumns = [
    { title: 'Project', dataIndex: 'consumer_name', key: 'consumer' },
    { title: 'Client', dataIndex: 'client_org_name', key: 'client' },
    { title: 'Platform', dataIndex: 'provider_name', key: 'provider' },
    {
      title: 'Active',
      key: 'active',
      render: (_: unknown, g: Grant) =>
        g.active ? <Tag color="green">yes</Tag> : <Tag>no</Tag>,
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <Title level={3} style={{ marginBottom: 4 }}>My API keys</Title>
          <Text type="secondary">
            Each project gets its own key. It only reaches clients an admin has granted it.
          </Text>
        </div>
        <Button type="primary" onClick={() => setOpen(true)}>New API key</Button>
      </div>

      <Card title="Projects (consumers)">
        <Table rowKey="id" dataSource={consumers} columns={consumerColumns} pagination={false} />
      </Card>

      <Card title="Access granted to my projects">
        <Table rowKey="id" dataSource={grants} columns={grantColumns} pagination={false} />
      </Card>

      <Modal
        title="New API key"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={isLoading}
        okText="Create"
      >
        <Form form={form} layout="vertical" onFinish={onCreate}>
          <Form.Item name="name" label="Project name" rules={[{ required: true }]}>
            <Input placeholder="e.g. shopify-operator" />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  )
}
