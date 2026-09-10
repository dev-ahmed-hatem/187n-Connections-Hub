import { StrictMode, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'
import { App as AntApp, ConfigProvider } from 'antd'

import App from './App'
import ErrorBoundary from '@/components/ErrorBoundary'
import { store } from '@/app/redux/store'
import { useAppSelector } from '@/app/redux/hooks'
import { darkTheme, lightTheme } from '@/theme/hubTheme'
import './index.css'
import '@/styles/hub.css'

function ThemedApp() {
  const dark = useAppSelector((s) => s.ui.dark)

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
  }, [dark])

  return (
    <ConfigProvider theme={dark ? darkTheme : lightTheme}>
      <AntApp>
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
      </AntApp>
    </ConfigProvider>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Provider store={store}>
      <BrowserRouter>
        <ThemedApp />
      </BrowserRouter>
    </Provider>
  </StrictMode>,
)
