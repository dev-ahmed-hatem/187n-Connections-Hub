import { useState } from 'react'
import {
  App,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'
import { DeleteOutlined, PlusOutlined, ReloadOutlined, TeamOutlined } from '@ant-design/icons'

import {
  useConsumersQuery,
  useCreateProjectMutation,
  useDeleteProjectMutation,
  useRotateKeyMutation,
  useUpdateProjectMutation,
} from '@/app/api/endpoints/access'
import { useOrgsQuery } from '@/app/api/endpoints/catalog'
import { useUsersQuery } from '@/app/api/endpoints/admin'
import type { Consumer } from '@/types'

const { Title, Text, Paragraph } = Typography

export default function AdminProjectsPage() {
  const { data: projects, isLoading } = useConsumersQuery()
  const { data: orgs } = useOrgsQuery()
  const { data: users } = useUsersQuery()
  const [createProject, { isLoading: creating }] = useCreateProjectMutation()
  const [updateProject] = useUpdateProjectMutation()
  const [rotateKey] = useRotateKeyMutation()
  const [deleteProject] = useDeleteProjectMutation()
  const { message, modal } = App.useApp()
  const [createForm] = Form.useForm()
  const [membersForm] = Form.useForm()
  const [createOpen, setCreateOpen] = useState(false)
  const [editProject, setEditProject] = useState<Consumer | null>(null)

  const developerOptions = (users ?? [])
    .filter((u) => u.role === 'developer')
    .map((u) => ({ value: u.id, label: u.username }))

  const showKey = (key: string) => modal.success({
    title: 'Project API key',
    content: <Paragraph copyable code style={{ wordBreak: 'break-all' }}>{key}</Paragraph>,
  })

  const onCreate = async (v: { name: string; client_org: number; members?: number[] }) => {
    try {
      const p = await createProject(v).unwrap()
      setCreateOpen(false); createForm.resetFields()
      showKey(p.api_key!)
    } catch { message.error('Could not create the project.') }
  }

  const openEdit = (p: Consumer) => {
    setEditProject(p)
    membersForm.setFieldsValue({ members: p.members })
  }
  const onSaveMembers = async (v: { members: number[] }) => {
    if (!editProject) return
    await updateProject({ id: editProject.id, members: v.members })
    setEditProject(null)
    message.success('Members updated.')
  }

  const onRotate = (p: Consumer) => modal.confirm({
    title: `Rotate key for "${p.name}"?`,
    onOk: async () => showKey((await rotateKey(p.id).unwrap()).api_key!),
  })

  const columns = [
    { title: 'Project', dataIndex: 'name', key: 'name' },
    { title: 'Client', dataIndex: 'client_org_name', key: 'client',
      render: (v: string) => v || <Text type="secondary">—</Text> },
    { title: 'Members', key: 'members',
      render: (_: unknown, p: Consumer) =>
        (p.member_usernames ?? []).length
          ? (p.member_usernames ?? []).map((u) => <Tag key={u}>{u}</Tag>)
          : <Text type="secondary">none</Text> },
    { title: 'Key', key: 'key', render: (_: unknown, p: Consumer) => <Text code>{p.api_key_prefix}…</Text> },
    { title: 'Status', key: 'active',
      render: (_: unknown, p: Consumer) => p.active ? <Tag color="green">active</Tag> : <Tag>inactive</Tag> },
    {
      title: 'Actions', key: 'actions',
      render: (_: unknown, p: Consumer) => (
        <Space>
          <Button size="small" icon={<TeamOutlined />} onClick={() => openEdit(p)}>Members</Button>
          <Button size="small" icon={<ReloadOutlined />} onClick={() => onRotate(p)}>Rotate key</Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() =>
            modal.confirm({
              title: `Delete project "${p.name}"?`,
              content: 'Its API key stops working immediately.',
              okButtonProps: { danger: true },
              onOk: async () => { await deleteProject(p.id).unwrap(); message.success('Project deleted.') },
            })
          } />
        </Space>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <Title level={3} style={{ marginBottom: 4 }}>Projects</Title>
          <Text type="secondary">
            A project is bound to one client and used by its assigned developers.
          </Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>New project</Button>
      </div>

      <Card>
        <Table rowKey="id" loading={isLoading} dataSource={projects} columns={columns} pagination={false} />
      </Card>

      <Modal title="New project" open={createOpen} onCancel={() => setCreateOpen(false)}
        onOk={() => createForm.submit()} confirmLoading={creating} okText="Create">
        <Form form={createForm} layout="vertical" onFinish={onCreate}>
          <Form.Item name="name" label="Project name" rules={[{ required: true }]}>
            <Input placeholder="e.g. shopify-restock-bot" />
          </Form.Item>
          <Form.Item name="client_org" label="Client" rules={[{ required: true }]}>
            <Select options={(orgs ?? []).map((o) => ({ value: o.id, label: o.name }))} />
          </Form.Item>
          <Form.Item name="members" label="Developers">
            <Select mode="multiple" options={developerOptions} placeholder="Assign developers" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title={editProject ? `Members · ${editProject.name}` : ''} open={!!editProject}
        onCancel={() => setEditProject(null)} onOk={() => membersForm.submit()} okText="Save">
        <Form form={membersForm} layout="vertical" onFinish={onSaveMembers}>
          <Form.Item name="members" label="Developers">
            <Select mode="multiple" options={developerOptions} />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  )
}
