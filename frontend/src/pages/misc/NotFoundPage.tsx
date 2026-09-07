import { Button, Result, Space } from 'antd'
import { useNavigate } from 'react-router-dom'

export default function NotFoundPage() {
  const navigate = useNavigate()
  return (
    <Result
      status="404"
      title="Page not found"
      subTitle="The page you're looking for doesn't exist or has moved."
      extra={
        <Space>
          <Button type="primary" onClick={() => navigate('/')}>Back to dashboard</Button>
          <Button onClick={() => navigate(-1)}>Go back</Button>
        </Space>
      }
    />
  )
}
