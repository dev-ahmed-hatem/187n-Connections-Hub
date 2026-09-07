import { useState } from 'react'
import { App, Button, Card, Input, Space, Tag, Typography } from 'antd'

import {
  useCommentsQuery,
  useCreateCommentMutation,
  useReopenNoteMutation,
  useResolveNoteMutation,
} from '@/app/api/endpoints/portal'
import type { Note } from '@/types'

const { Text, Paragraph } = Typography

export default function NoteThread({ note }: { note: Note }) {
  const { data: comments } = useCommentsQuery(note.id)
  const [createComment, { isLoading: sending }] = useCreateCommentMutation()
  const [resolveNote, { isLoading: resolving }] = useResolveNoteMutation()
  const [reopenNote, { isLoading: reopening }] = useReopenNoteMutation()
  const { message } = App.useApp()
  const [text, setText] = useState('')

  const send = async () => {
    if (!text.trim()) return
    await createComment({ note: note.id, body: text.trim() })
    setText('')
  }

  const open = note.status === 'open'

  return (
    <Card size="small">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <Tag color={note.type === 'blocker' ? 'red' : 'blue'}>{note.type}</Tag>
        <Text strong>{note.title}</Text>
        <Tag color={open ? 'gold' : 'green'}>{note.status}</Tag>
        <div style={{ flex: 1 }} />
        {open ? (
          <Button size="small" loading={resolving}
            onClick={async () => { await resolveNote(note.id); message.success('Resolved.') }}>
            Mark resolved
          </Button>
        ) : (
          <Button size="small" loading={reopening}
            onClick={async () => { await reopenNote(note.id); message.info('Reopened.') }}>
            Reopen
          </Button>
        )}
      </div>
      {note.body && <Paragraph style={{ marginBottom: 8 }}>{note.body}</Paragraph>}

      <Space direction="vertical" size={6} style={{ width: '100%' }}>
        {(comments ?? []).map((c) => (
          <div key={c.id} style={{ background: 'rgba(128,128,128,0.08)', borderRadius: 8,
            padding: '6px 10px' }}>
            <Text style={{ fontSize: 12 }} type="secondary">
              {c.author_username} · {new Date(c.created_at).toLocaleString()}
            </Text>
            <div>{c.body}</div>
          </div>
        ))}
      </Space>

      {open ? (
        <Space.Compact style={{ width: '100%', marginTop: 8 }}>
          <Input value={text} onChange={(e) => setText(e.target.value)} onPressEnter={send}
            placeholder="Write a reply…" />
          <Button type="primary" loading={sending} onClick={send}>Reply</Button>
        </Space.Compact>
      ) : (
        <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>
          This thread is resolved. Reopen it to reply.
        </Text>
      )}
    </Card>
  )
}
