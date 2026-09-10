import { theme } from 'antd'
import type { ThemeConfig } from 'antd'

// Adapted from 187N-ai/187n-site: design.css and Mission Control tokens.
const FONT = "'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
const MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"
const sharedToken = {
  colorPrimary: '#e2561f',
  colorInfo: '#548ed1',
  colorSuccess: '#4a9a6b',
  colorWarning: '#c99331',
  colorError: '#d85d51',
  borderRadius: 8,
  fontFamily: FONT,
  fontFamilyCode: MONO,
  fontSize: 14,
  controlHeight: 40,
  wireframe: false,
}
const sharedComponents = {
  Button: { borderRadius: 999, borderRadiusLG: 999, borderRadiusSM: 999,
    controlHeight: 40, primaryShadow: 'none', fontWeight: 600 },
  Card: { borderRadiusLG: 12 },
  Input: { borderRadius: 6, borderRadiusLG: 6, borderRadiusSM: 6, activeShadow: '0 0 0 2px #e2561f20' },
  InputNumber: { borderRadius: 6 },
  Select: { borderRadius: 6, borderRadiusLG: 6, borderRadiusSM: 6 },
  Tag: { borderRadiusSM: 4 },
  Segmented: { borderRadius: 6, borderRadiusSM: 4 },
  Modal: { borderRadiusLG: 12 },
  Menu: { itemBorderRadius: 6, itemHeight: 44 },
  Table: { borderRadiusLG: 8, headerBg: 'transparent' },
}
export const lightTheme: ThemeConfig = {
  algorithm: theme.defaultAlgorithm,
  token: { ...sharedToken, colorBgLayout: '#f4f2ee', colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff', colorText: '#161514', colorTextSecondary: '#66615b',
    colorTextTertiary: '#79736c', colorBorder: '#d9d5ce', colorBorderSecondary: '#e6e2db',
    colorPrimaryBg: '#fae9df', colorPrimaryBgHover: '#f6dacb' },
  components: { ...sharedComponents,
    Layout: { headerBg: '#f4f2ee', bodyBg: '#f4f2ee', siderBg: '#eeebe5' },
    Menu: { ...sharedComponents.Menu, itemSelectedBg: '#e2561f12', itemSelectedColor: '#aa3c13' } },
}
export const darkTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: { ...sharedToken, colorPrimary: '#ef6b34', colorBgLayout: '#0e0d0c',
    colorBgContainer: '#171513', colorBgElevated: '#201d19', colorText: '#f4f2ee',
    colorTextSecondary: '#b3ada5', colorTextTertiary: '#938b81', colorBorder: '#3c3731',
    colorBorderSecondary: '#2e2a25', colorPrimaryBg: '#e2561f18', colorPrimaryBgHover: '#e2561f26' },
  components: { ...sharedComponents,
    Layout: { headerBg: '#0e0d0c', bodyBg: '#0e0d0c', siderBg: '#12110f' },
    Menu: { ...sharedComponents.Menu, itemSelectedBg: '#e2561f18', itemSelectedColor: '#ff925f' } },
}
