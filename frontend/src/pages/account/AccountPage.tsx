import { App, Button, Card, Form, Input, Space, Typography } from 'antd'

import {
  useChangePasswordMutation,
  useUpdateProfileMutation,
} from '@/app/api/endpoints/account'
import { useAppDispatch, useAppSelector } from '@/app/redux/hooks'
import { setUser } from '@/app/slices/authSlice'

const { Title, Text } = Typography

export default function AccountPage() {
  const user = useAppSelector((s) => s.auth.user)
  const dispatch = useAppDispatch()
  const [updateProfile, { isLoading: savingProfile }] = useUpdateProfileMutation()
  const [changePassword, { isLoading: savingPw }] = useChangePasswordMutation()
  const { message } = App.useApp()
  const [pwForm] = Form.useForm()

  const onProfile = async (values: { first_name: string; last_name: string; email: string }) => {
    try {
      const updated = await updateProfile(values).unwrap()
      dispatch(setUser(updated))
      message.success('Profile updated.')
    } catch {
      message.error('Could not update profile.')
    }
  }

  const onPassword = async (values: { old_password: string; new_password: string }) => {
    try {
      await changePassword(values).unwrap()
      pwForm.resetFields()
      message.success('Password changed.')
    } catch (e) {
      const err = e as { data?: { detail?: string } }
      message.error(err?.data?.detail || 'Could not change password.')
    }
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%', maxWidth: 560 }}>
      <div>
        <Title level={3} style={{ marginBottom: 4 }}>Account</Title>
        <Text type="secondary">Manage your profile and password.</Text>
      </div>

      <Card title="Profile">
        <Form layout="vertical" onFinish={onProfile}
          initialValues={{ first_name: user?.first_name, last_name: user?.last_name,
            email: user?.email }}>
          <Space size="large" style={{ width: '100%' }} wrap>
            <Form.Item name="first_name" label="First name"><Input style={{ width: 220 }} /></Form.Item>
            <Form.Item name="last_name" label="Last name"><Input style={{ width: 220 }} /></Form.Item>
          </Space>
          <Form.Item name="email" label="Email" rules={[{ type: 'email' }]}>
            <Input style={{ maxWidth: 460 }} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={savingProfile}>Save profile</Button>
        </Form>
      </Card>

      <Card title="Change password">
        <Form form={pwForm} layout="vertical" onFinish={onPassword}>
          <Form.Item name="old_password" label="Current password" rules={[{ required: true }]}>
            <Input.Password style={{ maxWidth: 320 }} />
          </Form.Item>
          <Form.Item name="new_password" label="New password"
            rules={[{ required: true, min: 6 }]}>
            <Input.Password style={{ maxWidth: 320 }} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={savingPw}>Change password</Button>
        </Form>
      </Card>
    </Space>
  )
}
