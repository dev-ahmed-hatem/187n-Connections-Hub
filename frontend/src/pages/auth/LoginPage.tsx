import { useEffect } from 'react'
import { Alert, Button, Form, Input } from 'antd'
import { ArrowRightOutlined, LockOutlined } from '@ant-design/icons'
import { SiGoogleads, SiGoogleanalytics, SiMeta, SiShopify } from 'react-icons/si'
import { useNavigate } from 'react-router-dom'

import { useLoginMutation } from '@/app/api/endpoints/auth'
import { useAppDispatch, useAppSelector } from '@/app/redux/hooks'
import { setCredentials } from '@/app/slices/authSlice'

export default function LoginPage() {
  const [login, { isLoading, error }] = useLoginMutation()
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const user = useAppSelector((s) => s.auth.user)

  useEffect(() => { if (user) navigate('/') }, [user, navigate])
  const onFinish = async (values: { username: string; password: string }) => {
    try {
      const res = await login(values).unwrap()
      dispatch(setCredentials({ user: res.user, access: res.access, refresh: res.refresh }))
      navigate('/')
    } catch { /* displayed by the form */ }
  }

  return (
    <main className="hub-login">
      <section className="hub-login-story" aria-labelledby="login-heading">
        <a className="hub-login-brand" href="https://187n.ai" aria-label="187N website">
          <img src="/187n-infinity.png" alt="" width="64" height="33" />
          <span>187N<span className="hub-brand-divider">/</span><small>CONNECTIONS HUB</small></span>
        </a>
        <div className="hub-login-message">
          <p className="hub-eyebrow"><span /> YOUR GROWTH STARTS WITH CONNECTION.</p>
          <h1 id="login-heading">CONNECT<br /><span>ONCE.</span></h1>
          <p className="hub-login-handwriting">Move together.</p>
          <p className="hub-login-description">Your accounts. Your team. One place to bring<br className="hub-desktop-break" /> your business together.</p>
        </div>
        <div className="hub-login-platforms" aria-label="Platforms supported by the Hub">
          <span><SiShopify aria-hidden /> Shopify</span>
          <span><SiMeta aria-hidden /> Meta Ads</span>
          <span><SiGoogleads aria-hidden /> Google Ads</span>
          <span><SiGoogleanalytics aria-hidden /> Analytics</span>
        </div>
        <div className="hub-login-index" aria-hidden="true">01 — CONNECT / 02 — ALIGN / 03 — GROW</div>
      </section>
      <section className="hub-login-access" aria-labelledby="signin-heading">
        <div className="hub-login-access-top"><span className="hub-eyebrow">YOUR WORKSPACE</span><LockOutlined aria-hidden /></div>
        <div className="hub-login-form">
          <span className="hub-section-number" aria-hidden="true">[ 01 / ACCESS ]</span>
          <h2 id="signin-heading">Good to<br />have you here.</h2>
          <p>Sign in to manage your connections<br />and keep your team moving.</p>
          <Form layout="vertical" size="large" onFinish={onFinish} requiredMark={false}>
            <Form.Item name="username" label="Username" rules={[{ required: true, message: 'Enter your username.' }]}>
              <Input autoComplete="username" placeholder="Your personal username" />
            </Form.Item>
            <Form.Item name="password" label="Password" rules={[{ required: true, message: 'Enter your password.' }]}>
              <Input.Password autoComplete="current-password" placeholder="Your password" />
            </Form.Item>
            {error != null && <Alert type="error" showIcon className="hub-login-error" title="Could not sign in. Check your details and try again." />}
            <Button type="primary" htmlType="submit" block loading={isLoading} className="hub-login-submit">
              Enter workspace <ArrowRightOutlined />
            </Button>
          </Form>
          <p className="hub-login-help">Need access? Ask your 187N contact for a personal account.</p>
        </div>
        <footer className="hub-login-footer"><span>187N / CONNECTED OPERATIONS</span><span>Built to move forward. ↗</span></footer>
      </section>
    </main>
  )
}
