import { SiGoogleads, SiMeta, SiShopify } from 'react-icons/si'
import type { IconType } from 'react-icons'

import type { Provider } from '@/types'

const MAP: Record<string, { Icon: IconType; color: string }> = {
  'google-ads': { Icon: SiGoogleads, color: '#4285F4' },
  'meta-ads': { Icon: SiMeta, color: '#0467DF' },
  shopify: { Icon: SiShopify, color: '#95BF47' },
}

/** Official platform logo in a rounded tile; falls back to the provider's
 *  short-code letter on a colored tile for unknown providers. */
export default function ProviderIcon({
  provider,
  size = 26,
}: {
  provider: Provider
  size?: number
}) {
  const entry = MAP[provider.slug]
  const inner = Math.round(size * 0.62)
  return (
    <span
      style={{
        width: size,
        height: size,
        borderRadius: 8,
        display: 'inline-grid',
        placeItems: 'center',
        flex: 'none',
        background: entry ? '#fff' : provider.color || '#6c5ce7',
        border: entry ? '1px solid rgba(0,0,0,0.08)' : 'none',
        color: '#fff',
        fontWeight: 700,
        fontSize: Math.round(size * 0.46),
      }}
    >
      {entry ? (
        <entry.Icon size={inner} color={entry.color} />
      ) : (
        provider.short_code || provider.name[0]
      )}
    </span>
  )
}
