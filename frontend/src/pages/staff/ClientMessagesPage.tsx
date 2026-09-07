import { useState } from 'react'
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
import {
  useCreateAnnouncementMutation,
  useCreateNoteMutation,
  useNotesQuery,
} from '@/app/api/endpoints/portal'
import NoteThread from '@/components/NoteThread'
import type { Announcement } from '@/types'

const { Title, Text } = Typography

export default function ClientMessagesPage() {
  const { data: orgs } = useOrgsQuery()
  const [orgId, setOrgId] = useState<number | undefined>()
  const { data: notes } = useNotesQuery(orgId as number, { skip: !orgId })
  const [createNote, { isLoading: creatingNote }] = useCreateNoteMutation()
  const [createAnnouncement, { isLoading: posting }] = useCreateAnnouncementMutation()
  const { message } = App.useApp()
  const [noteForm] = Form.useForm()
  const [annForm] = Form.useForm()

  const onCreateNote = async (v: { type: string; title: string; body?: string }) => {
    if (!orgId) return
    try {
      await createNote({ client_org: orgId, ...v }).unwrap()
      noteForm.resetFields()
      message.success('Sent to client.')
    } catch { message.error('Could not create.') }
  }

  const onPostAnnouncement = async (v: Partial<Announcement>) => {
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
          Raise notes/blockers and post announcements; clients reply and resolve.
        </Text>
      </div>

      <Select placeholder="Select a client" style={{ minWidth: 280 }} value={orgId}
        onChange={setOrgId} options={(orgs ?? []).map((o) => ({ value: o.id, label: o.name }))} />

      <Card title="Post an announcement">
        <Form form={annForm} layout="vertical" onFinish={onPostAnnouncement}
          initialValues={{ audience: 'client_org', severity: 'info' }}>
          <Space wrap align="start">
            <Form.Item name="title" label="Title" rules={[{ required: true }]}>
              <Input style={{ minWidth: 260 }} />
            </Form.Item>
            <Form.Item name="audience" label="Audience">
              <Select style={{ minWidth: 170 }} options={[
                { value: 'client_org', label: 'This client', disabled: !orgId },
                { value: 'clients', label: 'All clients' },
                { value: 'all', label: 'Everyone' },
              ]} />
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
