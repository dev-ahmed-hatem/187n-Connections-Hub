import { theme } from 'antd'
import type { ThemeConfig } from 'antd'

// Frydai design tokens (see frydai app/marketing.css + dashboard.css dark block).
const FONT =
  "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
const MONO = "'Space Mono', ui-monospace, 'SF Mono', Menlo, Consolas, monospace"
const ACCENT = '#6c5ce7'

const sharedToken = {
  colorPrimary: ACCENT,
  colorInfo: ACCENT,
  colorSuccess: '#18a564',
  colorWarning: '#d98a23',
  colorError: '#e0556b',
  borderRadius: 12,
  fontFamily: FONT,
  fontFamilyCode: MONO,
  fontSize: 14,
  wireframe: false,
}

const sharedComponents = {
  Button: {
    borderRadius: 999,
    borderRadiusLG: 999,
    borderRadiusSM: 999,
    controlHeight: 38,
    primaryShadow: '0 14px 30px -12px rgba(108,92,231,0.55)',
  },
  Card: { borderRadiusLG: 18 },
  Input: { borderRadius: 12, borderRadiusLG: 12, borderRadiusSM: 10 },
  InputNumber: { borderRadius: 12 },
  Select: { borderRadius: 12, borderRadiusLG: 12, borderRadiusSM: 10 },
  Tag: { borderRadiusSM: 999 },
  Segmented: { borderRadius: 999, borderRadiusSM: 999 },
  Modal: { borderRadiusLG: 18 },
  Menu: { itemBorderRadius: 10, itemHeight: 40 },
  Table: { borderRadiusLG: 14, headerBg: 'transparent' },
}

export const lightTheme: ThemeConfig = {
  algorithm: theme.defaultAlgorithm,
  token: {
    ...sharedToken,
    colorBgLayout: '#f6f5fb',
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    colorText: '#16131f',
    colorTextSecondary: '#6a6680',
    colorTextTertiary: '#9a96a8',
    colorBorder: '#e2e0ec',
    colorBorderSecondary: '#ecebf2',
    colorPrimaryBg: '#efeaff',
    colorPrimaryBgHover: '#e6dfff',
  },
  components: {
    ...sharedComponents,
    Layout: { headerBg: '#ffffff', bodyBg: '#f6f5fb', siderBg: '#ffffff' },
    Menu: { ...sharedComponents.Menu, itemSelectedBg: '#efeaff', itemSelectedColor: '#4a3bc0' },
  },
}

export const darkTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    ...sharedToken,
    colorBgLayout: '#1a1724',
    colorBgContainer: '#121018',
    colorBgElevated: '#1a1724',
    colorText: '#f0ecf6',
    colorTextSecondary: '#b3adc4',
    colorTextTertiary: '#9a94ad',
    colorBorder: '#342f45',
    colorBorderSecondary: '#2a2638',
    colorPrimaryBg: 'rgba(108,92,231,0.18)',
    colorPrimaryBgHover: 'rgba(108,92,231,0.26)',
  },
  components: {
    ...sharedComponents,
    Layout: { headerBg: '#121018', bodyBg: '#1a1724', siderBg: '#121018' },
    Menu: {
      ...sharedComponents.Menu,
      itemSelectedBg: 'rgba(108,92,231,0.18)',
      itemSelectedColor: '#b8abf5',
    },
  },
}
