import { useMemo, useState } from 'react'
import {
  App,
  Button,
  Card,
  Empty,
  Form,
  Input,
  Select,
  Space,
  Typography,
} from 'antd'

import { useOrgsQuery } from '@/app/api/endpoints/catalog'
import { useConsumersQuery } from '@/app/api/endpoints/access'
import {
  useCreateAnnouncementMutation,
  useCreateNoteMutation,
  useNotesQuery,
} from '@/app/api/endpoints/portal'
import { useAppSelector } from '@/app/redux/hooks'
import NoteThread from '@/components/NoteThread'
import type { Announcement } from '@/types'

const { Title, Text } = Typography

export default function ClientMessagesPage() {
  const me = useAppSelector((s) => s.auth.user)
  const isAdmin = me?.role === 'admin'
  const { data: orgs } = useOrgsQuery(undefined, { skip: !isAdmin })
  const { data: projects } = useConsumersQuery(undefined, { skip: isAdmin })
  const [orgId, setOrgId] = useState<number | undefined>()
  const { data: notes } = useNotesQuery(orgId as number, { skip: !orgId })
  const [createNote, { isLoading: creatingNote }] = useCreateNoteMutation()
  const [createAnnouncement, { isLoading: posting }] = useCreateAnnouncementMutation()
  const { message } = App.useApp()
  const [noteForm] = Form.useForm()
  const [annForm] = Form.useForm()

  // Admins pick any client; developers only their assigned clients (via projects).
  const clientOptions = useMemo(() => {
    if (isAdmin) return (orgs ?? []).map((o) => ({ value: o.id, label: o.name }))
    const seen = new Map<number, string>()
    for (const p of projects ?? []) {
      if (p.client_org && !seen.has(p.client_org)) seen.set(p.client_org, p.client_org_name || '')
    }
    return [...seen].map(([id, name]) => ({ value: id, label: name }))
  }, [isAdmin, orgs, projects])

  const audienceOptions = [
    ...(orgId ? [{ value: 'client_org', label: 'This client' }] : []),
    { value: 'clients', label: 'All clients' },
    { value: 'all', label: 'Everyone' },
  ]

  const onCreateNote = async (v: { type: string; title: string; body?: string }) => {
    if (!orgId) return
    try {
      await createNote({ client_org: orgId, ...v }).unwrap()
      noteForm.resetFields()
      message.success('Sent to client.')
    } catch { message.error('Could not send.') }
  }

  const onPostAnnouncement = async (v: Partial<Announcement>) => {
    if (v.audience === 'client_org' && !orgId) {
      message.warning('Select a client first.')
      return
    }
    try {
      await createAnnouncement({
        ...v,
        client_org: v.audience === 'client_org' ? orgId : undefined,
        active: true,
      }).unwrap()
      annForm.resetFields()
      message.success('Announcement posted.')
    } catch { message.error('Could not post.') }
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={3} style={{ marginBottom: 4 }}>Client messages</Title>
        <Text type="secondary">
          Raise notes/blockers for a client; they reply and resolve.
          {isAdmin ? ' Post announcements to clients.' : ''}
        </Text>
      </div>

      <Select placeholder="Select a client" style={{ minWidth: 280 }} value={orgId}
        onChange={setOrgId} options={clientOptions}
        notFoundContent={isAdmin ? undefined : 'No assigned clients'} />

      {isAdmin && (
        <Card title="Post an announcement">
          <Form form={annForm} layout="vertical" onFinish={onPostAnnouncement}
            initialValues={{ audience: 'clients', severity: 'info' }}>
            <Space wrap align="start">
              <Form.Item name="title" label="Title" rules={[{ required: true }]}>
                <Input style={{ minWidth: 260 }} />
              </Form.Item>
              <Form.Item name="audience" label="Audience">
                <Select style={{ minWidth: 170 }} options={audienceOptions} />
              </Form.Item>
              <Form.Item name="severity" label="Severity">
                <Select style={{ minWidth: 130 }} options={[
                  { value: 'info', label: 'Info' },
                  { value: 'warning', label: 'Warning' },
                  { value: 'critical', label: 'Critical' },
                ]} />
              </Form.Item>
            </Space>
            <Form.Item name="body" label="Message"><Input.TextArea rows={2} /></Form.Item>
            <Button type="primary" htmlType="submit" loading={posting}>Post</Button>
          </Form>
        </Card>
      )}

      {orgId && (
        <>
          <Card title="Raise a note or blocker for this client">
            <Form form={noteForm} layout="vertical" onFinish={onCreateNote}
              initialValues={{ type: 'blocker' }}>
              <Space wrap align="start">
                <Form.Item name="type" label="Type">
                  <Select style={{ minWidth: 140 }} options={[
                    { value: 'blocker', label: 'Blocker' },
                    { value: 'note', label: 'Note' },
                  ]} />
                </Form.Item>
                <Form.Item name="title" label="Title" rules={[{ required: true }]}>
                  <Input style={{ minWidth: 280 }} />
                </Form.Item>
              </Space>
              <Form.Item name="body" label="Details"><Input.TextArea rows={2} /></Form.Item>
              <Button type="primary" htmlType="submit" loading={creatingNote}>Send</Button>
            </Form>
          </Card>

          <Card title="Threads">
            {(notes ?? []).length === 0 ? (
              <Empty description="No notes/blockers for this client yet" />
            ) : (
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {notes?.map((n) => <NoteThread key={n.id} note={n} />)}
              </Space>
            )}
          </Card>
        </>
      )}
    </Space>
  )
}
