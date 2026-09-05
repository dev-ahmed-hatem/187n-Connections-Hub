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
import ProviderIcon from '@/components/ProviderIcon'
import {
  useFetchTokenMutation,
  usePreviewDataMutation,
  useRequestConnectionMutation,
} from '@/app/api/endpoints/access'
import type { Account, Provider } from '@/types'

const { Title, Text, Paragraph } = Typography

const STATUS_COLOR: Record<string, string> = {
  connected: 'green',
  needs_reconnect: 'gold',
  not_connected: 'default',
}

interface Row {
  provider: Provider
  account?: Account
}

export default function DevAccessPage() {
  const { data: orgs } = useOrgsQuery()
  const [orgId, setOrgId] = useState<number | undefined>()
  const { data: overview, isFetching } = useOverviewQuery(orgId as number, { skip: !orgId })
  const [previewData, { isLoading: previewing }] = usePreviewDataMutation()
  const [fetchToken, { isLoading: tokening }] = useFetchTokenMutation()
  const [requestConnection] = useRequestConnectionMutation()
  const [testConnection] = useTestConnectionMutation()
  const { message } = App.useApp()
  const [result, setResult] = useState<{ title: string; body: unknown } | null>(null)
  const [testingId, setTestingId] = useState<number | null>(null)

  const onPreview = async (provider: string, accountId: string) => {
    try {
      const data = await previewData({ orgId: orgId!, provider, accountId }).unwrap()
      setResult({ title: `Data · ${provider} · ${accountId}`, body: data })
    } catch (e) { message.error(errText(e)) }
  }
  const onToken = async (provider: string, accountId: string) => {
    try {
      const data = await fetchToken({ orgId: orgId!, provider, accountId }).unwrap()
      setResult({ title: `Token · ${provider} · ${accountId}`, body: data })
    } catch (e) { message.error(errText(e)) }
  }
  const onRequest = async (provider: string) => {
    await requestConnection({ orgId: orgId!, provider, message: 'Please connect this platform.' })
    message.success('Connection request sent to the client.')
  }
  const onTest = async (connectionId: number) => {
    setTestingId(connectionId)
    try {
      const res = await testConnection(connectionId).unwrap()
      res.ok ? message.success('Connection is healthy.') : message.warning('Connection needs reconnect.')
    } finally {
      setTestingId(null)
    }
  }

  const rows: Row[] = (overview?.items ?? []).flatMap((it) =>
    it.accounts.length
      ? it.accounts.map((account) => ({ provider: it.provider, account }))
      : [{ provider: it.provider }],
  )

  const columns = [
    {
      title: 'Platform', key: 'provider',
      render: (_: unknown, r: Row) => (
        <Space><ProviderIcon provider={r.provider} />{r.provider.name}</Space>
      ),
    },
    {
      title: 'Account', key: 'account',
      render: (_: unknown, r: Row) =>
        r.account ? <Text code>{r.account.external_account_id}</Text> : <Text type="secondary">—</Text>,
    },
    {
      title: 'Status', key: 'status',
      render: (_: unknown, r: Row) => (
        <Tag color={STATUS_COLOR[r.account?.status ?? 'not_connected'] ?? 'default'}>
          {(r.account?.status ?? 'not_connected').replace('_', ' ')}
        </Tag>
      ),
    },
    {
      title: 'Actions', key: 'actions',
      render: (_: unknown, r: Row) =>
        r.account && r.account.status === 'connected' ? (
          <Space>
            <Button size="small" loading={previewing}
              onClick={() => onPreview(r.provider.slug, r.account!.external_account_id)}>
              Preview data
            </Button>
            <Button size="small" loading={tokening}
              onClick={() => onToken(r.provider.slug, r.account!.external_account_id)}>
              Fetch token
            </Button>
            <Button size="small"
              loading={testingId === r.account!.connection_id}
              disabled={testingId != null && testingId !== r.account!.connection_id}
              onClick={() => onTest(r.account!.connection_id)}>
              Test
            </Button>
          </Space>
        ) : (
          <Button size="small" type="primary" ghost onClick={() => onRequest(r.provider.slug)}>
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
          Pick a client, then pull data or a short-lived token for a specific account — no client
          credentials ever leave the hub.
        </Text>
      </div>

      <Select placeholder="Select a client" style={{ minWidth: 280 }} value={orgId}
        onChange={setOrgId} options={(orgs ?? []).map((o) => ({ value: o.id, label: o.name }))} />

      {orgId && (
        <Card loading={isFetching}>
          <Table rowKey={(r) => `${r.provider.id}-${r.account?.connection_id ?? 'none'}`}
            dataSource={rows} columns={columns} pagination={false} />
        </Card>
      )}

      <Drawer title={result?.title} open={!!result} onClose={() => setResult(null)} width={440}>
        <Paragraph type="secondary">Returned by the hub:</Paragraph>
        <pre style={{ background: 'rgba(128,128,128,0.12)', padding: 12, borderRadius: 8,
          overflow: 'auto' }}>
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
