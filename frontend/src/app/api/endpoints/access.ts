import { apiSlice } from '@/app/api/apiSlice'
import type { AuditLog, Consumer, Grant } from '@/types'

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
    audit: build.query<AuditLog[], number | void>({
      query: (clientOrg) => ({
        url: '/access/audit/',
        method: 'get',
        params: clientOrg ? { client_org: clientOrg } : undefined,
      }),
      providesTags: ['Audit'],
    }),
    // Interactive developer-portal actions:
    previewData: build.mutation<
      Record<string, unknown>,
      { orgId: number; provider: string }
    >({
      query: ({ orgId, provider }) => ({
        url: `/access/clients/${orgId}/${provider}/data`,
        method: 'get',
      }),
      invalidatesTags: ['Audit'],
    }),
    fetchToken: build.mutation<TokenResponse, { orgId: number; provider: string }>({
      query: ({ orgId, provider }) => ({
        url: `/access/clients/${orgId}/${provider}/token`,
        method: 'post',
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
  useGrantsQuery,
  useCreateGrantMutation,
  useDeleteGrantMutation,
  useAuditQuery,
  usePreviewDataMutation,
  useFetchTokenMutation,
  useRequestConnectionMutation,
} = accessApi
