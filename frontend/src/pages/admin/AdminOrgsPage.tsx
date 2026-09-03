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

import { useCreateOrgMutation, useOrgsQuery } from '@/app/api/endpoints/catalog'
import { useCreateUserMutation, useUsersQuery } from '@/app/api/endpoints/admin'
import type { ClientOrg, User } from '@/types'

const { Title, Text } = Typography

function slugify(name: string) {
  return name.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
}

export default function AdminOrgsPage() {
  const { data: orgs } = useOrgsQuery()
  const { data: users } = useUsersQuery()
  const [createOrg, { isLoading: creatingOrg }] = useCreateOrgMutation()
  const [createUser, { isLoading: creatingUser }] = useCreateUserMutation()
  const { message } = App.useApp()
  const [orgForm] = Form.useForm()
  const [userForm] = Form.useForm()

  const onCreateOrg = async (values: { name: string }) => {
    try {
      await createOrg({ name: values.name, slug: slugify(values.name) }).unwrap()
      orgForm.resetFields()
      message.success('Client created.')
    } catch {
      message.error('Could not create the client.')
    }
  }

  const onCreateUser = async (values: {
    username: string
    password: string
    role: string
    client_org?: number
  }) => {
    try {
      await createUser(values).unwrap()
      userForm.resetFields()
      message.success('User created.')
    } catch {
      message.error('Could not create the user.')
    }
  }

  const orgColumns = [
    { title: 'Client', dataIndex: 'name', key: 'name' },
    { title: 'Slug', dataIndex: 'slug', key: 'slug',
      render: (s: string) => <Text code>{s}</Text> },
  ]
  const userColumns = [
    { title: 'Username', dataIndex: 'username', key: 'username' },
    {
      title: 'Role', key: 'role',
      render: (_: unknown, u: User) => <Tag>{u.role}</Tag>,
    },
    { title: 'Client', dataIndex: 'client_org_name', key: 'client' },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={3} style={{ margin: 0 }}>Clients &amp; users</Title>

      <Card title="Add a client">
        <Form form={orgForm} layout="inline" onFinish={onCreateOrg}>
          <Form.Item name="name" rules={[{ required: true }]}>
            <Input placeholder="Client name" style={{ minWidth: 240 }} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={creatingOrg}>Add client</Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="Clients">
        <Table rowKey="id" dataSource={orgs as ClientOrg[]} columns={orgColumns} pagination={false} />
      </Card>

      <Card title="Add a user">
        <Form form={userForm} layout="inline" onFinish={onCreateUser}>
          <Form.Item name="username" rules={[{ required: true }]}>
            <Input placeholder="Username" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true }]}>
            <Input.Password placeholder="Password" />
          </Form.Item>
          <Form.Item name="role" rules={[{ required: true }]}>
            <Select placeholder="Role" style={{ minWidth: 140 }} options={[
              { value: 'client', label: 'Client' },
              { value: 'developer', label: 'Developer' },
              { value: 'admin', label: 'Admin' },
            ]} />
          </Form.Item>
          <Form.Item name="client_org">
            <Select allowClear placeholder="Client (if client role)" style={{ minWidth: 180 }}
              options={(orgs ?? []).map((o) => ({ value: o.id, label: o.name }))} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={creatingUser}>Add user</Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="Users">
        <Table rowKey="id" dataSource={users} columns={userColumns} pagination={false} />
      </Card>
    </Space>
  )
}
