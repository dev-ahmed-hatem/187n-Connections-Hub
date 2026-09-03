import { Button, Card, Tag, Typography } from 'antd'

import type { ConnectionStatus, OverviewItem } from '@/types'

const { Text } = Typography

const STATUS: Record<ConnectionStatus, { color: string; label: string }> = {
  connected: { color: 'green', label: 'Connected' },
  needs_reconnect: { color: 'gold', label: 'Needs reconnect' },
  not_connected: { color: 'default', label: 'Not connected' },
  disconnected: { color: 'default', label: 'Disconnected' },
  error: { color: 'red', label: 'Error' },
}

export default function ConnectionStatusCard({
  item,
  onConnect,
  onReconnect,
  loading,
}: {
  item: OverviewItem
  onConnect?: (slug: string) => void
  onReconnect?: (slug: string) => void
  loading?: boolean
}) {
  const s = STATUS[item.status] ?? STATUS.not_connected
  const p = item.provider
  const isConnected = item.status === 'connected'

  return (
    <Card size="small" style={{ height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
        <div
          style={{
            width: 40, height: 40, borderRadius: 10, display: 'grid',
            placeItems: 'center', color: '#fff', fontWeight: 800, fontSize: 16,
            background: p.color || '#4f56d6',
          }}
        >
          {p.short_code || p.name[0]}
        </div>
        <div style={{ lineHeight: 1.2 }}>
          <div style={{ fontWeight: 600 }}>{p.name}</div>
          {item.external_account_id ? (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {item.external_account_id}
            </Text>
          ) : (
            <Text type="secondary" style={{ fontSize: 12 }}>
              No account linked
            </Text>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Tag color={s.color}>{s.label}</Tag>
        {onConnect &&
          (isConnected ? (
            onReconnect && (
              <Button size="small" loading={loading} onClick={() => onReconnect(p.slug)}>
                Reconnect
              </Button>
            )
          ) : (
            <Button
              size="small"
              type="primary"
              loading={loading}
              onClick={() =>
                item.status === 'needs_reconnect'
                  ? onReconnect?.(p.slug)
                  : onConnect(p.slug)
              }
            >
              {item.status === 'needs_reconnect' ? 'Reconnect' : 'Connect'}
            </Button>
          ))}
      </div>
    </Card>
  )
}
