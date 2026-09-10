import { useEffect, useState } from 'react'
import { Alert, App, Col, Input, Modal, Row, Space, Spin, Tag, Typography } from 'antd'
import { useSearchParams } from 'react-router-dom'

import {
  useDeleteConnectionMutation,
  useOverviewQuery,
  useStartConnectionMutation,
  useTestConnectionMutation,
} from '@/app/api/endpoints/connections'
import ProviderConnectionsCard from '@/components/ProviderConnectionsCard'



export default function ClientConnectionsPage() {
  const { data, isLoading, refetch } = useOverviewQuery()
  const [startConnection, { isLoading: starting }] = useStartConnectionMutation()
  const [testConnection] = useTestConnectionMutation()
  const [deleteConnection] = useDeleteConnectionMutation()
  const [params, setParams] = useSearchParams()
  const { message } = App.useApp()
  const [shopModalOpen, setShopModalOpen] = useState(false)
  const [shop, setShop] = useState('')
  const [testingId, setTestingId] = useState<number | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  useEffect(() => {
    if (params.get('connected')) {
      message.success(`Connected ${params.get('connected')} successfully.`)
      refetch()
      setParams({}, { replace: true })
    } else if (params.get('error')) {
      message.error(`Connection failed: ${params.get('error')}`)
      setParams({}, { replace: true })
    }
  }, [params, message, refetch, setParams])

  const connect = async (provider: string, providerParams?: Record<string, string>) => {
    if (provider === 'shopify' && !providerParams?.shop) {
      setShopModalOpen(true)
      return
    }
    try {
      const res = await startConnection({ provider, params: providerParams }).unwrap()
      window.location.href = res.authorize_url
    } catch {
      message.error('Could not start the connection.')
    }
  }

  const confirmShop = () => {
    if (!shop.trim()) return
    setShopModalOpen(false)
    connect('shopify', { shop: shop.trim() })
  }

  const onTest = async (connectionId: number) => {
    setTestingId(connectionId)
    try {
      const res = await testConnection(connectionId).unwrap()
      if (res.ok) message.success('Data response received. Full audit verification is separate.')
      else message.warning('Data could not be verified. Check this connection’s permissions.')
    } catch {
      message.error('The connection test could not be completed.')
    } finally {
      setTestingId(null)
    }
  }

  const onDelete = async (connectionId: number) => {
    setDeletingId(connectionId)
    try {
      await deleteConnection(connectionId).unwrap()
      message.success('Account disconnected.')
    } catch {
      message.error('Could not disconnect the account.')
    } finally {
      setDeletingId(null)
    }
  }

  const needsReconnect = (data?.items ?? [])
    .flatMap((it) => it.accounts.filter((a) => a.status === 'needs_reconnect').map(() => it.provider.name))

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div className="hub-page-intro">
        <div>
          <span className="hub-section-number">02 / YOUR CONNECTIONS</span>
          <h1>Bring it<br /><em>together.</em></h1>
          <p>Connect your business accounts once. Choose what to share and give your team the access they need.</p>
        </div>
      </div>

      {needsReconnect.length > 0 && (
        <Alert type="warning" showIcon
          message="Some connections need reconnecting"
          description={`Please reconnect: ${[...new Set(needsReconnect)].join(', ')}.`} />
      )}

      <div className="hub-connections-legend">
        <span><Tag color="blue">Authorized</Tag> data verification is separate</span>
        <span><Tag color="gold">Needs reconnect</Tag> re-approve access</span>
        <span><Tag>Not connected</Tag> awaiting your permission</span>
      </div>

      {isLoading ? (
        <Spin />
      ) : (
        <Row gutter={[16, 16]}>
          {data?.items.map((item) => (
            <Col xs={24} md={12} key={item.provider.id}>
              <ProviderConnectionsCard
                item={item}
                connecting={starting}
                testingId={testingId}
                deletingId={deletingId}
                onConnect={connect}
                onReconnect={connect}
                onTest={onTest}
                onDelete={onDelete}
              />
            </Col>
          ))}
        </Row>
      )}

      <Modal title="Connect Shopify" open={shopModalOpen}
        onCancel={() => setShopModalOpen(false)} onOk={confirmShop} okText="Continue">
        <Typography.Paragraph type="secondary">
          Enter your store domain to continue to Shopify's consent screen.
        </Typography.Paragraph>
        <Input placeholder="your-store.myshopify.com" value={shop}
          onChange={(e) => setShop(e.target.value)} onPressEnter={confirmShop} autoFocus />
      </Modal>
    </Space>
  )
}
