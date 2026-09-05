import { useState } from 'react'
import {
  App,
  Button,
  Card,
  Drawer,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'

import { useOrgsQuery } from '@/app/api/endpoints/catalog'
import { useOverviewQuery, useTestConnectionMutation } from '@/app/api/endpoints/connections'
import {
  useFetchTokenMutation,
  usePreviewDataMutation,
  useRequestConnectionMutation,
} from '@/app/api/endpoints/access'
import type { OverviewItem } from '@/types'

const { Title, Text, Paragraph } = Typography

const STATUS_COLOR: Record<string, string> = {
  connected: 'green',
  needs_reconnect: 'gold',
  not_connected: 'default',
}

export default function DevAccessPage() {
  const { data: orgs } = useOrgsQuery()
  const [orgId, setOrgId] = useState<number | undefined>()
  const { data: overview, isFetching } = useOverviewQuery(orgId as number, { skip: !orgId })
  const [previewData, { isLoading: previewing }] = usePreviewDataMutation()
  const [fetchToken, { isLoading: tokening }] = useFetchTokenMutation()
  const [requestConnection] = useRequestConnectionMutation()
  const [testConnection, { isLoading: testing }] = useTestConnectionMutation()
  const { message } = App.useApp()

  const [result, setResult] = useState<{ title: string; body: unknown } | null>(null)

  const onPreview = async (provider: string) => {
    try {
      const data = await previewData({ orgId: orgId!, provider }).unwrap()
      setResult({ title: `Data · ${provider}`, body: data })
    } catch (e) {
      message.error(errText(e))
    }
  }
  const onToken = async (provider: string) => {
    try {
      const data = await fetchToken({ orgId: orgId!, provider }).unwrap()
      setResult({ title: `Access token · ${provider}`, body: data })
    } catch (e) {
      message.error(errText(e))
    }
  }
  const onRequest = async (provider: string) => {
    await requestConnection({ orgId: orgId!, provider, message: 'Please connect this platform.' })
    message.success('Connection request sent to the client.')
  }
  const onTest = async (connectionId: number) => {
    const res = await testConnection(connectionId).unwrap()
    res.ok ? message.success('Connection is healthy.') : message.warning('Connection needs reconnect.')
  }

  const columns = [
    {
      title: 'Platform',
      key: 'provider',
      render: (_: unknown, item: OverviewItem) => (
        <Space>
          <span style={{
            width: 26, height: 26, borderRadius: 7, display: 'inline-grid',
            placeItems: 'center', color: '#fff', fontWeight: 700, fontSize: 12,
            background: item.provider.color || '#4f56d6',
          }}>
            {item.provider.short_code || item.provider.name[0]}
          </span>
          {item.provider.name}
        </Space>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      render: (_: unknown, item: OverviewItem) => (
        <Tag color={STATUS_COLOR[item.status] ?? 'default'}>
          {item.status.replace('_', ' ')}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: unknown, item: OverviewItem) =>
        item.status === 'connected' ? (
          <Space>
            <Button size="small" loading={previewing} onClick={() => onPreview(item.provider.slug)}>
              Preview data
            </Button>
            <Button size="small" loading={tokening} onClick={() => onToken(item.provider.slug)}>
              Fetch token
            </Button>
            {item.connection_id && (
              <Button size="small" loading={testing} onClick={() => onTest(item.connection_id!)}>
                Test
              </Button>
            )}
          </Space>
        ) : (
          <Button size="small" type="primary" ghost onClick={() => onRequest(item.provider.slug)}>
            Request connection
          </Button>
        ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={3} style={{ marginBottom: 4 }}>Client access</Title>
        <Text type="secondary">
          Pick a client, then pull data or a short-lived token — no client credentials ever leave the hub.
        </Text>
      </div>

      <Select
        placeholder="Select a client"
        style={{ minWidth: 280 }}
        value={orgId}
        onChange={setOrgId}
        options={(orgs ?? []).map((o) => ({ value: o.id, label: o.name }))}
      />

      {orgId && (
        <Card loading={isFetching}>
          <Table
            rowKey={(r) => r.provider.id}
            dataSource={overview?.items}
            columns={columns}
            pagination={false}
          />
        </Card>
      )}

      <Drawer
        title={result?.title}
        open={!!result}
        onClose={() => setResult(null)}
        width={440}
      >
        <Paragraph type="secondary">Returned by the hub (mock data / token):</Paragraph>
        <pre style={{ background: '#f6f6f6', padding: 12, borderRadius: 8, overflow: 'auto' }}>
          {JSON.stringify(result?.body, null, 2)}
        </pre>
      </Drawer>
    </Space>
  )
}

function errText(e: unknown): string {
  const err = e as { data?: { detail?: string } }
  return err?.data?.detail || 'Request failed.'
}
