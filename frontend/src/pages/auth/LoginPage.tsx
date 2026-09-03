import { useEffect } from 'react'
import { Alert, Button, Card, Form, Input, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'

import { useLoginMutation } from '@/app/api/endpoints/auth'
import { useAppDispatch, useAppSelector } from '@/app/redux/hooks'
import { setCredentials } from '@/app/slices/authSlice'

const { Title, Text } = Typography

export default function LoginPage() {
  const [login, { isLoading, error }] = useLoginMutation()
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const user = useAppSelector((s) => s.auth.user)

  useEffect(() => {
    if (user) navigate('/')
  }, [user, navigate])

  const onFinish = async (values: { username: string; password: string }) => {
    try {
      const res = await login(values).unwrap()
      dispatch(setCredentials({ user: res.user, access: res.access, refresh: res.refresh }))
      navigate('/')
    } catch {
      /* handled by error state */
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center',
      background: '#f4f5f7' }}>
      <Card style={{ width: 380 }}>
        <Title level={3} style={{ marginBottom: 4 }}>Connections Hub</Title>
        <Text type="secondary">Sign in to continue</Text>
        <Form layout="vertical" onFinish={onFinish} style={{ marginTop: 20 }}>
          <Form.Item name="username" label="Username" rules={[{ required: true }]}>
            <Input autoFocus placeholder="e.g. admin, dev, northwind" />
          </Form.Item>
          <Form.Item name="password" label="Password" rules={[{ required: true }]}>
            <Input.Password placeholder="••••••••" />
          </Form.Item>
          {error != null && (
            <Alert type="error" showIcon style={{ marginBottom: 12 }}
              message="Invalid username or password." />
          )}
          <Button type="primary" htmlType="submit" block loading={isLoading}>
            Sign in
          </Button>
        </Form>
        <Text type="secondary" style={{ display: 'block', marginTop: 16, fontSize: 12 }}>
          Demo: admin/admin123 · dev/dev12345 · northwind/client123
        </Text>
      </Card>
    </div>
  )
}
