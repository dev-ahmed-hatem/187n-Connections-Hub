import { Button, Card, Empty, Popconfirm, Space, Tag, Typography } from 'antd'
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons'

import ProviderIcon from '@/components/ProviderIcon'
import type { Account, ConnectionStatus, ProviderAccounts } from '@/types'

const { Text } = Typography

const STATUS: Record<ConnectionStatus, { color: string; label: string }> = {
  connected: { color: 'blue', label: 'Authorized · audit unverified' },
  needs_reconnect: { color: 'gold', label: 'Needs reconnect' },
  not_connected: { color: 'default', label: 'Not connected' },
  disconnected: { color: 'default', label: 'Disconnected' },
  error: { color: 'red', label: 'Error' },
}

export default function ProviderConnectionsCard({
  item,
  connecting,
  testingId,
  deletingId,
  onConnect,
  onReconnect,
  onTest,
  onDelete,
}: {
  item: ProviderAccounts
  connecting?: boolean
  testingId?: number | null
  deletingId?: number | null
  onConnect: (slug: string) => void
  onReconnect: (slug: string) => void
  onTest: (connectionId: number) => void
  onDelete: (connectionId: number) => void
}) {
  const p = item.provider
  const hasAccounts = item.accounts.length > 0
  const aTestRunning = testingId != null

  return (
    <Card
      size="small"
      style={{ height: '100%' }}
      title={<Space><ProviderIcon provider={p} />{p.name}</Space>}
      extra={
        <Button size="small" type={hasAccounts ? 'default' : 'primary'}
          icon={<PlusOutlined />} loading={connecting} onClick={() => onConnect(p.slug)}>
          {hasAccounts ? 'Connect another' : 'Connect'}
        </Button>
      }
    >
      {!hasAccounts ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No accounts connected" />
      ) : (
        <Space direction="vertical" style={{ width: '100%' }} size={8}>
          {item.accounts.map((a: Account) => {
            const s = STATUS[a.status] ?? STATUS.not_connected
            return (
              <div key={a.connection_id}
                style={{ display: 'flex', alignItems: 'center', gap: 8,
                  justifyContent: 'space-between' }}>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden',
                    textOverflow: 'ellipsis' }}>{a.display_name || a.external_account_id}</div>
                  <Text type="secondary" style={{ fontSize: 12 }}>{a.external_account_id}</Text>
                </div>
                <Space size={6}>
                  <Tag color={s.color}>{s.label}</Tag>
                  {a.status === 'connected' && (
                    <Button
                      size="small"
                      loading={testingId === a.connection_id}
                      disabled={aTestRunning && testingId !== a.connection_id}
                      onClick={() => onTest(a.connection_id)}
                    >
                      Test
                    </Button>
                  )}
                  {a.status === 'needs_reconnect' && (
                    <Button size="small" type="primary" loading={connecting}
                      onClick={() => onReconnect(p.slug)}>
                      Reconnect
                    </Button>
                  )}
                  <Popconfirm
                    title="Disconnect this account?"
                    description="Projects using it will lose access."
                    okText="Disconnect" okButtonProps={{ danger: true }}
                    onConfirm={() => onDelete(a.connection_id)}
                  >
                    <Button size="small" danger icon={<DeleteOutlined />}
                      loading={deletingId === a.connection_id} />
                  </Popconfirm>
                </Space>
              </div>
            )
          })}
        </Space>
      )}
    </Card>
  )
}
