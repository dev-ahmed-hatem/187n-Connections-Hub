import { Button, Result } from 'antd'
import { useNavigate } from 'react-router-dom'

export default function ForbiddenPage() {
  const navigate = useNavigate()
  return (
    <Result
      status="403"
      title="You don't have access"
      subTitle="This page isn't available for your role. Contact an admin if you think this is a mistake."
      extra={<Button type="primary" onClick={() => navigate('/')}>Back to dashboard</Button>}
    />
  )
}
