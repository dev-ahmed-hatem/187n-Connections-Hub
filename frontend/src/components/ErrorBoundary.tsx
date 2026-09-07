import { Component } from 'react'
import type { ReactNode } from 'react'
import { Button, Result, Space } from 'antd'

interface Props {
  children: ReactNode
}
interface State {
  hasError: boolean
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: unknown) {
    // eslint-disable-next-line no-console
    console.error('Unhandled UI error:', error)
  }

  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="Something went wrong"
          subTitle="An unexpected error occurred. Reloading usually fixes it."
          extra={
            <Space>
              <Button type="primary" onClick={() => window.location.reload()}>
                Reload
              </Button>
              <Button onClick={() => { window.location.href = '/' }}>
                Back to dashboard
              </Button>
            </Space>
          }
        />
      )
    }
    return this.props.children
  }
}
