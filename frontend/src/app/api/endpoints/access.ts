import { apiSlice } from '@/app/api/apiSlice'
import type {
  AuditLog,
  Consumer,
  ConsumerAccess,
  Grant,
  GrantRequest,
  Paginated,
} from '@/types'

interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  provider: string
  external_account_id: string
  login_customer_id?: string
}

export const accessApi = apiSlice.injectEndpoints({
  endpoints: (build) => ({
    consumers: build.query<Consumer[], void>({
      query: () => ({ url: '/access/consumers/', method: 'get' }),
      providesTags: ['Consumers'],
    }),
    createConsumer: build.mutation<Consumer, { name: string }>({
      query: (body) => ({ url: '/access/consumers/', method: 'post', data: body }),
      invalidatesTags: ['Consumers'],
    }),
    deleteConsumer: build.mutation<void, number>({
      query: (id) => ({ url: `/access/consumers/${id}/`, method: 'delete' }),
      invalidatesTags: ['Consumers'],
    }),
    rotateKey: build.mutation<Consumer, number>({
      query: (id) => ({ url: `/access/consumers/${id}/rotate-key/`, method: 'post' }),
      invalidatesTags: ['Consumers'],
    }),
    consumerAccess: build.query<ConsumerAccess, number>({
      query: (id) => ({ url: `/access/consumers/${id}/access/`, method: 'get' }),
      providesTags: ['Grants', 'Connections'],
    }),
    grants: build.query<Grant[], void>({
      query: () => ({ url: '/access/grants/', method: 'get' }),
      providesTags: ['Grants'],
    }),
    createGrant: build.mutation<
      Grant,
      { consumer: number; client_org: number; provider: number; scopes?: string[] }
    >({
      query: (body) => ({ url: '/access/grants/', method: 'post', data: body }),
      invalidatesTags: ['Grants'],
    }),
    deleteGrant: build.mutation<void, number>({
      query: (id) => ({ url: `/access/grants/${id}/`, method: 'delete' }),
      invalidatesTags: ['Grants'],
    }),
    grantRequests: build.query<GrantRequest[], void>({
      query: () => ({ url: '/access/grant-requests/', method: 'get' }),
      providesTags: ['GrantRequests'],
    }),
    createGrantRequest: build.mutation<
      GrantRequest,
      { consumer: number; client_org: number; provider: number; scopes?: string[]; message?: string }
    >({
      query: (body) => ({ url: '/access/grant-requests/', method: 'post', data: body }),
      invalidatesTags: ['GrantRequests'],
    }),
    approveGrantRequest: build.mutation<GrantRequest, number>({
      query: (id) => ({ url: `/access/grant-requests/${id}/approve/`, method: 'post' }),
      invalidatesTags: ['GrantRequests', 'Grants'],
    }),
    denyGrantRequest: build.mutation<GrantRequest, number>({
      query: (id) => ({ url: `/access/grant-requests/${id}/deny/`, method: 'post' }),
      invalidatesTags: ['GrantRequests'],
    }),
    audit: build.query<
      Paginated<AuditLog>,
      { page?: number; page_size?: number; status?: string; client_org?: number }
    >({
      query: (params) => ({ url: '/access/audit/', method: 'get', params }),
      providesTags: ['Audit'],
    }),
    // Interactive developer-portal actions:
    previewData: build.mutation<
      Record<string, unknown>,
      { orgId: number; provider: string; accountId?: string }
    >({
      query: ({ orgId, provider, accountId }) => ({
        url: `/access/clients/${orgId}/${provider}/data`,
        method: 'get',
        params: accountId ? { account_id: accountId } : undefined,
      }),
      invalidatesTags: ['Audit'],
    }),
    fetchToken: build.mutation<
      TokenResponse,
      { orgId: number; provider: string; accountId?: string }
    >({
      query: ({ orgId, provider, accountId }) => ({
        url: `/access/clients/${orgId}/${provider}/token`,
        method: 'post',
        data: accountId ? { account_id: accountId } : undefined,
      }),
      invalidatesTags: ['Audit'],
    }),
    requestConnection: build.mutation<
      { id: number; status: string },
      { orgId: number; provider: string; message?: string }
    >({
      query: ({ orgId, provider, message }) => ({
        url: `/access/clients/${orgId}/${provider}/request-connection`,
        method: 'post',
        data: { message },
      }),
      invalidatesTags: ['Requests', 'Audit'],
    }),
  }),
})

export const {
  useConsumersQuery,
  useCreateConsumerMutation,
  useDeleteConsumerMutation,
  useRotateKeyMutation,
  useConsumerAccessQuery,
  useGrantsQuery,
  useCreateGrantMutation,
  useDeleteGrantMutation,
  useGrantRequestsQuery,
  useCreateGrantRequestMutation,
  useApproveGrantRequestMutation,
  useDenyGrantRequestMutation,
  useAuditQuery,
  usePreviewDataMutation,
  useFetchTokenMutation,
  useRequestConnectionMutation,
} = accessApi
