import { useEffect } from 'react'
import { App, Col, Row, Space, Spin, Tag, Typography } from 'antd'
import { useSearchParams } from 'react-router-dom'

import { useOverviewQuery, useStartConnectionMutation } from '@/app/api/endpoints/connections'
import ConnectionStatusCard from '@/components/ConnectionStatusCard'

const { Title, Text } = Typography

export default function ClientConnectionsPage() {
  const { data, isLoading, refetch } = useOverviewQuery()
  const [startConnection, { isLoading: starting }] = useStartConnectionMutation()
  const [params, setParams] = useSearchParams()
  const { message } = App.useApp()

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

  const connect = async (provider: string) => {
    try {
      const res = await startConnection({ provider }).unwrap()
      window.location.href = res.authorize_url
    } catch {
      message.error('Could not start the connection.')
    }
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={3} style={{ marginBottom: 4 }}>Your connections</Title>
        <Text type="secondary">
          Connect each platform once. We keep the connection alive so your operators can use it.
        </Text>
      </div>

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
                onConnect={connect}
                onReconnect={connect}
              />
            </Col>
          ))}
        </Row>
      )}
    </Space>
  )
}
