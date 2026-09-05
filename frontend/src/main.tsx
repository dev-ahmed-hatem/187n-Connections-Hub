import { StrictMode, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import { BrowserRouter } from 'react-router-dom'
import { App as AntApp, ConfigProvider } from 'antd'

// Frydai fonts (self-hosted)
import '@fontsource/plus-jakarta-sans/400.css'
import '@fontsource/plus-jakarta-sans/500.css'
import '@fontsource/plus-jakarta-sans/600.css'
import '@fontsource/plus-jakarta-sans/700.css'
import '@fontsource/plus-jakarta-sans/800.css'
import '@fontsource/space-mono/400.css'
import '@fontsource/space-mono/700.css'

import App from './App'
import ErrorBoundary from '@/components/ErrorBoundary'
import { store } from '@/app/redux/store'
import { useAppSelector } from '@/app/redux/hooks'
import { darkTheme, lightTheme } from '@/theme/frydaiTheme'
import './index.css'
import '@/styles/frydai.css'

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
