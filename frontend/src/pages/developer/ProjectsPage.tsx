import { useMemo, useState } from 'react'
import {
  App,
  Button,
  Card,
  Drawer,
  Empty,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'
import { KeyOutlined, ReloadOutlined, SafetyOutlined } from '@ant-design/icons'

import {
  useConsumersQuery,
  useCreateProjectRequestMutation,
  useFetchTokenMutation,
  usePreviewDataMutation,
  useProjectAccessQuery,
  useRequestableProjectsQuery,
  useProjectRequestsQuery,
  useRotateKeyMutation,
} from '@/app/api/endpoints/access'
import { useTestConnectionMutation } from '@/app/api/endpoints/connections'
import ProviderIcon from '@/components/ProviderIcon'
import type { Consumer } from '@/types'

const { Title, Text, Paragraph } = Typography

const STATUS_COLOR: Record<string, string> = {
  connected: 'green', needs_reconnect: 'gold', not_connected: 'default',
}

export default function ProjectsPage() {
  const { data: projects, isLoading } = useConsumersQuery()
  const { data: requests } = useProjectRequestsQuery()
  const { data: requestable } = useRequestableProjectsQuery()
  const [rotateKey] = useRotateKeyMutation()
  const [createRequest, { isLoading: requesting }] = useCreateProjectRequestMutation()
  const { message, modal } = App.useApp()

  const [clientFilter, setClientFilter] = useState<string | undefined>()
  const [openProject, setOpenProject] = useState<Consumer | null>(null)
  const [requestOpen, setRequestOpen] = useState(false)
  const [reqForm] = Form.useForm()

  const clients = useMemo(
    () => [...new Set((projects ?? []).map((p) => p.client_org_name).filter(Boolean))] as string[],
    [projects],
  )
  const rows = (projects ?? []).filter((p) => !clientFilter || p.client_org_name === clientFilter)
  const pending = (requests ?? []).filter((r) => r.status === 'pending')

  const showKey = (key: string) => modal.success({
    title: 'New API key',
    content: <Paragraph copyable code style={{ wordBreak: 'break-all' }}>{key}</Paragraph>,
  })

  const onRotate = (p: Consumer) => modal.confirm({
    title: `Rotate key for "${p.name}"?`,
    content: 'The current key stops working immediately.',
    onOk: async () => showKey((await rotateKey(p.id).unwrap()).api_key!),
  })

  const onRequest = async (v: { consumer: number; message?: string }) => {
    try {
      await createRequest(v).unwrap()
      setRequestOpen(false); reqForm.resetFields()
      message.success('Access request sent for approval.')
    } catch { message.error('Could not send the request.') }
  }

  const columns = [
    { title: 'Project', dataIndex: 'name', key: 'name' },
    { title: 'Client', dataIndex: 'client_org_name', key: 'client',
      render: (v: string) => v || <Text type="secondary">—</Text> },
    { title: 'Key', key: 'key', render: (_: unknown, p: Consumer) => <Text code>{p.api_key_prefix}…</Text> },
    { title: 'Status', key: 'active',
      render: (_: unknown, p: Consumer) => p.active ? <Tag color="green">active</Tag> : <Tag>inactive</Tag> },
    {
      title: 'Actions', key: 'actions',
      render: (_: unknown, p: Consumer) => (
        <Space>
          <Button size="small" icon={<SafetyOutlined />} onClick={() => setOpenProject(p)}>Open</Button>
          <Button size="small" icon={<ReloadOutlined />} onClick={() => onRotate(p)}>Rotate key</Button>
        </Space>
      ),
    },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div style={{ flex: 1 }}>
          <Title level={3} style={{ marginBottom: 4 }}>My projects</Title>
          <Text type="secondary">
            Open a project to fetch keys/data for its client's connected platforms.
          </Text>
        </div>
        <Button icon={<KeyOutlined />} onClick={() => setRequestOpen(true)}>Request access</Button>
      </div>

      {clients.length > 0 && (
        <Select allowClear placeholder="Filter by client" style={{ minWidth: 240 }}
          value={clientFilter} onChange={setClientFilter}
          options={clients.map((c) => ({ value: c, label: c }))} />
      )}

      <Card>
        <Table rowKey="id" loading={isLoading} dataSource={rows} columns={columns}
          pagination={false}
          locale={{ emptyText: <Empty description="No projects yet — request access to one" /> }} />
      </Card>

      {pending.length > 0 && (
        <Card title="My pending access requests">
          <Space direction="vertical" style={{ width: '100%' }}>
            {pending.map((r) => (
              <Text key={r.id}><Tag color="gold">pending</Tag> {r.consumer_name}
                {r.client_org_name ? ` · ${r.client_org_name}` : ''}</Text>
            ))}
          </Space>
        </Card>
      )}

      <Drawer title={openProject ? `Project · ${openProject.name}` : ''} open={!!openProject}
        onClose={() => setOpenProject(null)} width={520}>
        {openProject && <ProjectPanel project={openProject} />}
      </Drawer>

      <Modal title="Request project access" open={requestOpen} onCancel={() => setRequestOpen(false)}
        onOk={() => reqForm.submit()} confirmLoading={requesting} okText="Send request">
        <Form form={reqForm} layout="vertical" onFinish={onRequest}>
          <Form.Item name="consumer" label="Project" rules={[{ required: true }]}>
            <Select showSearch optionFilterProp="label"
              options={(requestable ?? []).map((p) => ({
                value: p.id, label: `${p.name}${p.client_org_name ? ` · ${p.client_org_name}` : ''}` }))} />
          </Form.Item>
          <Form.Item name="message" label="Message (optional)"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>
    </Space>
  )
}

function ProjectPanel({ project }: { project: Consumer }) {
  const { data, isLoading } = useProjectAccessQuery(project.id)
  const [previewData, { isLoading: previewing }] = usePreviewDataMutation()
  const [fetchToken, { isLoading: tokening }] = useFetchTokenMutation()
  const [testConnection] = useTestConnectionMutation()
  const { message } = App.useApp()
  const [result, setResult] = useState<{ title: string; body: unknown } | null>(null)
  const [testingId, setTestingId] = useState<number | null>(null)

  const orgId = data?.client_org ?? undefined

  const preview = async (provider: string, accountId: string) => {
    try {
      const d = await previewData({ orgId: orgId!, provider, accountId }).unwrap()
      setResult({ title: `Data · ${provider}`, body: d })
    } catch (e) { message.error(errText(e)) }
  }
  const token = async (provider: string, accountId: string) => {
    try {
      const d = await fetchToken({ orgId: orgId!, provider, accountId }).unwrap()
      setResult({ title: `Token · ${provider}`, body: d })
    } catch (e) { message.error(errText(e)) }
  }
  const test = async (id: number) => {
    setTestingId(id)
    try {
      const r = await testConnection(id).unwrap()
      r.ok ? message.success('Healthy.') : message.warning('Needs reconnect.')
    } finally { setTestingId(null) }
  }

  if (isLoading) return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Loading…" />

  return (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      <Text type="secondary">Client: <b>{data?.client_org_name || '—'}</b> · key <Text code>{project.api_key_prefix}…</Text></Text>
      {data?.platforms.map((g) => (
        <Card key={g.provider.id} size="small"
          title={<Space><ProviderIcon provider={g.provider} />{g.provider.name}</Space>}>
          {g.accounts.length === 0 ? (
            <Text type="secondary">Not connected</Text>
          ) : (
            <Space direction="vertical" style={{ width: '100%' }} size={8}>
              {g.accounts.map((a) => (
                <div key={a.connection_id} style={{ display: 'flex', alignItems: 'center', gap: 8,
                  justifyContent: 'space-between' }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 600 }}>{a.external_account_id}</div>
                    <Tag color={STATUS_COLOR[a.status] ?? 'default'}>{a.status.replace('_', ' ')}</Tag>
                  </div>
                  {a.status === 'connected' && (
                    <Space size={4}>
                      <Button size="small" loading={previewing}
                        onClick={() => preview(g.provider.slug, a.external_account_id)}>Data</Button>
                      <Button size="small" loading={tokening}
                        onClick={() => token(g.provider.slug, a.external_account_id)}>Token</Button>
                      <Button size="small" loading={testingId === a.connection_id}
                        onClick={() => test(a.connection_id)}>Test</Button>
                    </Space>
                  )}
                </div>
              ))}
            </Space>
          )}
        </Card>
      ))}

      <Modal title={result?.title} open={!!result} onCancel={() => setResult(null)} footer={null}>
        <pre style={{ background: 'rgba(128,128,128,0.12)', padding: 12, borderRadius: 8,
          overflow: 'auto' }}>{JSON.stringify(result?.body, null, 2)}</pre>
      </Modal>
    </Space>
  )
}

function errText(e: unknown): string {
  const err = e as { data?: { detail?: string } }
  return err?.data?.detail || 'Request failed.'
}
