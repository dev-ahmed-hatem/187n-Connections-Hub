import { App, Alert, Button, Card, Empty, List, Space, Tag, Typography } from 'antd'

import {
  useAnnouncementsQuery,
  useNotesQuery,
  useRequestsQuery,
  useUpdateNoteMutation,
  useUpdateRequestMutation,
} from '@/app/api/endpoints/portal'
import { useStartConnectionMutation } from '@/app/api/endpoints/connections'

const { Title, Text } = Typography

const SEVERITY: Record<string, 'info' | 'warning' | 'error'> = {
  info: 'info',
  warning: 'warning',
  critical: 'error',
}

export default function ClientUpdatesPage() {
  const { data: announcements } = useAnnouncementsQuery()
  const { data: notes } = useNotesQuery()
  const { data: requests } = useRequestsQuery()
  const [resolveNote] = useUpdateNoteMutation()
  const [updateRequest] = useUpdateRequestMutation()
  const [startConnection] = useStartConnectionMutation()
  const { message } = App.useApp()

  const pendingRequests = (requests ?? []).filter((r) => r.status === 'pending')
  const openNotes = (notes ?? []).filter((n) => n.status === 'open')

  const connect = async (provider: string) => {
    const res = await startConnection({ provider }).unwrap()
    window.location.href = res.authorize_url
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Title level={3} style={{ margin: 0 }}>Updates &amp; blockers</Title>

      <Card title="Announcements">
        {(announcements ?? []).length === 0 ? (
          <Empty description="No announcements" />
        ) : (
          <Space direction="vertical" style={{ width: '100%' }}>
            {announcements?.map((a) => (
              <Alert key={a.id} type={SEVERITY[a.severity] ?? 'info'} showIcon
                message={a.title} description={a.body} />
            ))}
          </Space>
        )}
      </Card>

      <Card title="Connection requests from the team">
        {pendingRequests.length === 0 ? (
          <Empty description="No pending requests" />
        ) : (
          <List
            dataSource={pendingRequests}
            renderItem={(r) => (
              <List.Item
                actions={[
                  <Button key="c" type="primary" onClick={() => connect(r.provider_slug)}>
                    Connect
                  </Button>,
                  <Button
                    key="d"
                    onClick={async () => {
                      await updateRequest({ id: r.id, status: 'declined' })
                      message.info('Request declined.')
                    }}
                  >
                    Decline
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={`Connect ${r.provider_name}`}
                  description={r.message || 'A developer requested this connection.'}
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      <Card title="Blockers &amp; notes">
        {openNotes.length === 0 ? (
          <Empty description="Nothing needs your attention" />
        ) : (
          <List
            dataSource={openNotes}
            renderItem={(n) => (
              <List.Item
                actions={[
                  <Button key="r" onClick={() => resolveNote({ id: n.id, status: 'resolved' })}>
                    Mark resolved
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <Tag color={n.type === 'blocker' ? 'red' : 'blue'}>{n.type}</Tag>
                      {n.title}
                    </Space>
                  }
                  description={n.body}
                />
              </List.Item>
            )}
          />
        )}
      </Card>
      <Text type="secondary">Resolved items and completed requests are hidden.</Text>
    </Space>
  )
}
