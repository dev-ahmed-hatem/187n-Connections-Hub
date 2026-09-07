export type Role = 'admin' | 'developer' | 'client'

export interface Paginated<T> {
  count: number
  page: number
  page_size: number
  total_pages: number
  next: string | null
  previous: string | null
  results: T[]
}

export type ConnectionStatus =
  | 'connected'
  | 'needs_reconnect'
  | 'disconnected'
  | 'error'
  | 'not_connected'

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: Role
  client_org: number | null
  client_org_name?: string
  is_active: boolean
}

export interface Provider {
  id: number
  slug: string
  name: string
  short_code: string
  color: string
  scopes: string[]
  is_mock: boolean
  is_active: boolean
}

export interface Account {
  connection_id: number
  external_account_id: string
  display_name: string
  status: ConnectionStatus
  last_checked: string | null
}

export interface ProviderAccounts {
  provider: Provider
  accounts: Account[]
}

export interface ConnectionOverview {
  client_org: number
  client_org_name: string
  items: ProviderAccounts[]
}

export interface ClientOrg {
  id: number
  name: string
  slug: string
  notes: string
  created_at: string
}

export interface Consumer {
  id: number
  name: string
  client_org: number | null
  client_org_name?: string
  members: number[]
  member_usernames?: string[]
  api_key_prefix: string
  active: boolean
  created_at: string
  api_key?: string // present only on creation
}

export interface ProjectAccessGroup {
  provider: Provider
  accounts: Account[]
}

export interface ProjectAccess {
  consumer: number
  consumer_name: string
  client_org: number | null
  client_org_name: string | null
  platforms: ProjectAccessGroup[]
}

export interface RequestableProject {
  id: number
  name: string
  client_org_name: string | null
}

export interface ProjectAccessRequest {
  id: number
  consumer: number
  consumer_name: string
  client_org_name?: string
  message: string
  status: 'pending' | 'approved' | 'denied'
  requested_by: number | null
  requested_by_username?: string
  decided_at: string | null
  created_at: string
}

export interface Announcement {
  id: number
  audience: 'all' | 'clients' | 'client_org'
  client_org: number | null
  client_org_name?: string
  title: string
  body: string
  severity: 'info' | 'warning' | 'critical'
  active: boolean
  created_at: string
}

export interface Note {
  id: number
  client_org: number
  client_org_name?: string
  connection: number | null
  type: 'blocker' | 'note'
  title: string
  body: string
  status: 'open' | 'resolved'
  created_at: string
}

export interface ConnectionRequest {
  id: number
  requested_by: number | null
  requested_by_username?: string
  client_org: number
  client_org_name?: string
  provider: number
  provider_name: string
  provider_slug: string
  message: string
  status: 'pending' | 'connected' | 'declined'
  created_at: string
  resolved_at: string | null
}

export interface DashboardSummary {
  role: Role
  [key: string]: unknown
}

export interface Comment {
  id: number
  note: number
  author: number | null
  author_username?: string
  author_role?: Role
  body: string
  created_at: string
}

export interface Notification {
  id: number
  actor: number | null
  actor_username?: string
  kind: string
  title: string
  body: string
  url: string
  read: boolean
  created_at: string
}

export interface AuditLog {
  id: number
  actor_type: string
  actor_label: string
  action: string
  client_org: number | null
  client_org_name?: string
  provider: number | null
  provider_slug?: string
  status: string
  meta: Record<string, unknown>
  created_at: string
}
