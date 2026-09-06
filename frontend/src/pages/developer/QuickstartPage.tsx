import { useState } from 'react'
import { Alert, Card, Select, Space, Tabs, Typography } from 'antd'
import { ApiOutlined } from '@ant-design/icons'

import { useOrgsQuery, useProvidersQuery } from '@/app/api/endpoints/catalog'

const { Title, Text, Paragraph, Link } = Typography

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000/api'

export default function QuickstartPage() {
  const { data: orgs } = useOrgsQuery()
  const { data: providers } = useProvidersQuery()
  const [orgId, setOrgId] = useState<number | undefined>()
  const [provider, setProvider] = useState<string | undefined>()

  const org = orgId ?? '<CLIENT_ID>'
  const prov = provider ?? '<PROVIDER>'
  const dataUrl = `${API_BASE}/access/clients/${org}/${prov}/data?range=last_30d`
  const tokenUrl = `${API_BASE}/access/clients/${org}/${prov}/token`

  const curl = `# Fetch data (data-proxy)
curl "${dataUrl}" \\
  -H "Authorization: ApiKey YOUR_API_KEY"

# Fetch a short-lived token (token-broker)
curl -X POST "${tokenUrl}" \\
  -H "Authorization: ApiKey YOUR_API_KEY"`

  const python = `import requests

BASE = "${API_BASE}"
HEADERS = {"Authorization": "ApiKey YOUR_API_KEY"}

# Data-proxy
r = requests.get(f"{BASE}/access/clients/${org}/${prov}/data",
                 params={"range": "last_30d"}, headers=HEADERS)
print(r.json())

# Token-broker
t = requests.post(f"{BASE}/access/clients/${org}/${prov}/token", headers=HEADERS)
print(t.json()["access_token"])`

  const js = `const BASE = "${API_BASE}";
const headers = { Authorization: "ApiKey YOUR_API_KEY" };

// Data-proxy
const data = await fetch(
  \`\${BASE}/access/clients/${org}/${prov}/data?range=last_30d\`,
  { headers }
).then((r) => r.json());

// Token-broker
const { access_token } = await fetch(
  \`\${BASE}/access/clients/${org}/${prov}/token\`,
  { method: "POST", headers }
).then((r) => r.json());`

  const base = `${API_BASE}/access/clients/${org}/google-ads/data`
  const googleResources = `# Google Analytics (GA4) — list properties, then report
GET ${base}?resource=analytics
GET ${base}?resource=analytics&property_id=123456789

# Search Console — list sites, then query
GET ${base}?resource=search-console
GET ${base}?resource=search-console&site_url=https://example.com/

# Merchant Center — list accessible merchant accounts
GET ${base}?resource=merchant

# Google Ads (needs developer token)
GET ${base}?resource=ads`

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={3} style={{ marginBottom: 4 }}>Quickstart &amp; API</Title>
        <Text type="secondary">
          Call the hub from any project with your project's API key. Full reference at{' '}
          <Link href={`${API_BASE.replace(/\/api$/, '')}/api/docs/`} target="_blank">
            <ApiOutlined /> /api/docs
          </Link>.
        </Text>
      </div>

      <Alert type="info" showIcon
        message="Your project only ever holds a key to the hub"
        description="The hub returns finished data or a ~1-hour token — never the client's long-lived credentials. Create a project on the Projects page to get a key; an admin approves which clients it can reach." />

      <Card title="Pick a client & platform to template the snippets">
        <Space wrap>
          <Select placeholder="Client" style={{ minWidth: 220 }} value={orgId} onChange={setOrgId}
            options={(orgs ?? []).map((o) => ({ value: o.id, label: o.name }))} />
          <Select placeholder="Platform" style={{ minWidth: 200 }} value={provider} onChange={setProvider}
            options={(providers ?? []).map((p) => ({ value: p.slug, label: p.name }))} />
        </Space>
      </Card>

      <Card>
        <Tabs
          items={[
            { key: 'curl', label: 'curl', children: <CodeBlock code={curl} /> },
            { key: 'python', label: 'Python', children: <CodeBlock code={python} /> },
            { key: 'js', label: 'JavaScript', children: <CodeBlock code={js} /> },
          ]}
        />
      </Card>

      <Card title="Google: pick a service with ?resource=">
        <Paragraph type="secondary">
          The Google connector spans several services. On the data endpoint, pass{' '}
          <Text code>resource</Text> — call without an id to list, then with the id to report.
          (Ads needs a developer token; Analytics/Search Console/Merchant work with the OAuth token.)
        </Paragraph>
        <CodeBlock code={googleResources} />
      </Card>
    </Space>
  )
}

function CodeBlock({ code }: { code: string }) {
  return (
    <Paragraph copyable={{ text: code }}>
      <pre style={{ margin: 0, padding: 12, borderRadius: 8, overflow: 'auto',
        background: 'rgba(128,128,128,0.12)' }}>
        <code>{code}</code>
      </pre>
    </Paragraph>
  )
}
