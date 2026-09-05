import { useEffect, useState } from 'react'
import { Alert, App, Col, Input, Modal, Row, Space, Spin, Tag, Typography } from 'antd'
import { useSearchParams } from 'react-router-dom'

import {
  useOverviewQuery,
  useStartConnectionMutation,
  useTestConnectionMutation,
} from '@/app/api/endpoints/connections'
import ConnectionStatusCard from '@/components/ConnectionStatusCard'

const { Title, Text } = Typography

export default function ClientConnectionsPage() {
  const { data, isLoading, refetch } = useOverviewQuery()
  const [startConnection, { isLoading: starting }] = useStartConnectionMutation()
  const [testConnection, { isLoading: testing }] = useTestConnectionMutation()
  const [params, setParams] = useSearchParams()
  const { message } = App.useApp()
  const [shopModalOpen, setShopModalOpen] = useState(false)
  const [shop, setShop] = useState('')

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
    // Shopify needs the store domain before we can build the authorize URL.
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
    const res = await testConnection(connectionId).unwrap()
    res.ok ? message.success('Connection is healthy.') : message.warning('This connection needs reconnecting.')
  }

  const needsReconnect = (data?.items ?? []).filter((i) => i.status === 'needs_reconnect')

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={3} style={{ marginBottom: 4 }}>Your connections</Title>
        <Text type="secondary">
          Connect each platform once. We keep the connection alive so your operators can use it.
        </Text>
      </div>

      {needsReconnect.length > 0 && (
        <Alert
          type="warning"
          showIcon
          message="Some connections need reconnecting"
          description={`Please reconnect: ${needsReconnect.map((i) => i.provider.name).join(', ')}.`}
        />
      )}

      <Space size="large" wrap>
        <span><Tag color="green">Connected</Tag> ready to use</span>
        <span><Tag color="gold">Needs reconnect</Tag> please re-approve</span>
        <span><Tag>Not connected</Tag> connect to enable</span>
      </Space>

      {isLoading ? (
        <Spin />
      ) : (
        <Row gutter={[16, 16]}>
          {data?.items.map((item) => (
            <Col xs={24} sm={12} lg={8} key={item.provider.id}>
              <ConnectionStatusCard
                item={item}
                loading={starting}
                testing={testing}
                onConnect={connect}
                onReconnect={connect}
                onTest={onTest}
              />
            </Col>
          ))}
        </Row>
      )}

      <Modal
        title="Connect Shopify"
        open={shopModalOpen}
        onCancel={() => setShopModalOpen(false)}
        onOk={confirmShop}
        okText="Continue"
      >
        <Typography.Paragraph type="secondary">
          Enter your store domain to continue to Shopify's consent screen.
        </Typography.Paragraph>
        <Input
          placeholder="your-store.myshopify.com"
          value={shop}
          onChange={(e) => setShop(e.target.value)}
          onPressEnter={confirmShop}
          autoFocus
        />
      </Modal>
    </Space>
  )
}
