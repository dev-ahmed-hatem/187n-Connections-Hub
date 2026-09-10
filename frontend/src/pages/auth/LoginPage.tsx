import { useEffect } from 'react'
import { Alert, Button, Card, Form, Input, Typography } from 'antd'
import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

import { useLoginMutation } from '@/app/api/endpoints/auth'
import { useAppDispatch, useAppSelector } from '@/app/redux/hooks'
import { setCredentials } from '@/app/slices/authSlice'

const { Text } = Typography

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
    <div
      style={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        padding: 16,
        background:
          'radial-gradient(900px 380px at 12% -12%, var(--accent-soft), transparent 60%),' +
          'radial-gradient(720px 340px at 100% 112%, var(--accent-soft), transparent 62%),' +
          'var(--bg-soft)',
      }}
    >
      <Card
        style={{ width: 408, boxShadow: 'var(--shadow-card)' }}
        styles={{ body: { padding: 30 } }}
      >
        {/* Brand header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 13, marginBottom: 22 }}>
          <span className="hub-brand-tile" style={{ width: 44, height: 44, borderRadius: 13 }}>
            <img src="/brand-mark.svg" alt="" style={{ width: 28, height: 28 }} />
          </span>
          <div style={{ lineHeight: 1.2 }}>
            <div style={{ fontSize: 19, fontWeight: 800, letterSpacing: '-0.02em' }}>
              <span style={{ color: 'var(--accent)' }}>187n</span> Connections Hub
            </div>
            <Text type="secondary" style={{ fontSize: 12.5 }}>
              Connect once. Operate anywhere.
            </Text>
          </div>
        </div>

        <Form layout="vertical" size="large" onFinish={onFinish} requiredMark={false}>
          <Form.Item name="username" label="Username" rules={[{ required: true }]}>
            <Input autoFocus prefix={<UserOutlined />} placeholder="Your personal username" autoComplete="username" />
          </Form.Item>
          <Form.Item name="password" label="Password" rules={[{ required: true }]}
            style={{ marginBottom: 12 }}>
            <Input.Password autoComplete="current-password" prefix={<LockOutlined />} placeholder="••••••••" />
          </Form.Item>
          {error != null && (
            <Alert type="error" showIcon style={{ marginBottom: 14 }}
              message="Invalid username or password." />
          )}
          <Button type="primary" htmlType="submit" block loading={isLoading}>
            Sign in
          </Button>
        </Form>


      </Card>
    </div>
  )
}
