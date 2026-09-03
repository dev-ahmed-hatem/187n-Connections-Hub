import {
  App,
  Button,
  Card,
  Form,
  Input,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'

import {
  useAnnouncementsQuery,
  useCreateAnnouncementMutation,
} from '@/app/api/endpoints/portal'
import type { Announcement } from '@/types'

const { Title } = Typography

const SEV_COLOR: Record<string, string> = {
  info: 'blue',
  warning: 'gold',
  critical: 'red',
}

export default function AdminAnnouncementsPage() {
  const { data: announcements } = useAnnouncementsQuery()
  const [create, { isLoading }] = useCreateAnnouncementMutation()
  const { message } = App.useApp()
  const [form] = Form.useForm()

  const onCreate = async (values: Partial<Announcement>) => {
    try {
      await create({ ...values, active: true }).unwrap()
      form.resetFields()
      message.success('Announcement posted.')
    } catch {
      message.error('Could not post the announcement.')
    }
  }

  const columns = [
    { title: 'Title', dataIndex: 'title', key: 'title' },
    { title: 'Audience', dataIndex: 'audience', key: 'audience' },
    {
      title: 'Severity', key: 'severity',
      render: (_: unknown, a: Announcement) => (
        <Tag color={SEV_COLOR[a.severity]}>{a.severity}</Tag>
      ),
    },
    {
      title: 'Active', key: 'active',
      render: (_: unknown, a: Announcement) =>
        a.active ? <Tag color="green">yes</Tag> : <Tag>no</Tag>,
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={3} style={{ margin: 0 }}>Announcements</Title>

      <Card title="Post an announcement">
        <Form form={form} layout="vertical" onFinish={onCreate}
          initialValues={{ audience: 'all', severity: 'info' }}>
          <Space wrap align="start">
            <Form.Item name="title" label="Title" rules={[{ required: true }]}>
              <Input style={{ minWidth: 260 }} placeholder="Title" />
            </Form.Item>
            <Form.Item name="audience" label="Audience">
              <Select style={{ minWidth: 160 }} options={[
                { value: 'all', label: 'Everyone' },
                { value: 'clients', label: 'All clients' },
              ]} />
            </Form.Item>
            <Form.Item name="severity" label="Severity">
              <Select style={{ minWidth: 140 }} options={[
                { value: 'info', label: 'Info' },
                { value: 'warning', label: 'Warning' },
                { value: 'critical', label: 'Critical' },
              ]} />
            </Form.Item>
          </Space>
          <Form.Item name="body" label="Message">
            <Input.TextArea rows={3} placeholder="Message body" />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={isLoading}>Post</Button>
        </Form>
      </Card>

      <Card title="All announcements">
        <Table rowKey="id" dataSource={announcements} columns={columns} pagination={false} />
      </Card>
    </Space>
  )
}
