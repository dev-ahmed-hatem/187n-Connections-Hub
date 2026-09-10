import { Badge, Button, Empty, List, Popover, Typography } from 'antd'
import { BellOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  useMarkAllNotificationsReadMutation,
  useMarkNotificationReadMutation,
  useNotificationsQuery,
  useUnreadCountQuery,
} from '@/app/api/endpoints/portal'
import type { Notification } from '@/types'

const { Text } = Typography

export default function NotificationsBell() {
  const { data: unread } = useUnreadCountQuery(undefined, { pollingInterval: 30000 })
  const { data: items } = useNotificationsQuery(undefined, { pollingInterval: 60000 })
  const [markRead] = useMarkNotificationReadMutation()
  const [markAll] = useMarkAllNotificationsReadMutation()
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  const onClick = async (n: Notification) => {
    if (!n.read) await markRead(n.id)
    setOpen(false)
    if (n.url) navigate(n.url)
  }

  const content = (
    <div style={{ width: 'min(340px, calc(100vw - 48px))', maxHeight: 420, overflow: 'auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: 8 }}>
        <Text strong>Notifications</Text>
        <Button type="link" size="small" onClick={() => markAll()}>Mark all read</Button>
      </div>
      {(items ?? []).length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Nothing yet" />
      ) : (
        <List
          size="small"
          dataSource={items}
          renderItem={(n) => (
            <List.Item
              style={{ cursor: 'pointer', background: n.read ? undefined : 'var(--accent-soft)',
                borderRadius: 8, paddingInline: 8 }}
              onClick={() => onClick(n)}
            >
              <List.Item.Meta
                title={<span style={{ fontWeight: n.read ? 400 : 600 }}>{n.title}</span>}
                description={
                  <span style={{ fontSize: 12 }}>
                    {n.body ? `${n.body.slice(0, 80)} · ` : ''}
                    {new Date(n.created_at).toLocaleString()}
                  </span>
                }
              />
            </List.Item>
          )}
        />
      )}
    </div>
  )

  return (
    <Popover content={content} trigger="click" open={open} onOpenChange={setOpen}
      placement="bottomRight">
      <Badge count={unread?.count ?? 0} size="small">
        <Button type="text" aria-label="Notifications" icon={<BellOutlined />} />
      </Badge>
    </Popover>
  )
}
