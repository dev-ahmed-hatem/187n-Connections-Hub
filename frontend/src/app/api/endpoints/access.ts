import { apiSlice } from '@/app/api/apiSlice'
import type {
  AuditLog,
  Consumer,
  Paginated,
  ProjectAccess,
  ProjectAccessRequest,
  RequestableProject,
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
    // --- Projects (consumers) ---
    consumers: build.query<Consumer[], void>({
      query: () => ({ url: '/access/consumers/', method: 'get' }),
      providesTags: ['Consumers'],
    }),
    createProject: build.mutation<
      Consumer,
      { name: string; client_org: number; members?: number[] }
    >({
      query: (body) => ({ url: '/access/consumers/', method: 'post', data: body }),
      invalidatesTags: ['Consumers'],
    }),
    updateProject: build.mutation<
      Consumer,
      { id: number; client_org?: number; members?: number[]; active?: boolean }
    >({
      query: ({ id, ...body }) => ({ url: `/access/consumers/${id}/`, method: 'patch', data: body }),
      invalidatesTags: ['Consumers'],
    }),
    rotateKey: build.mutation<Consumer, number>({
      query: (id) => ({ url: `/access/consumers/${id}/rotate-key/`, method: 'post' }),
      invalidatesTags: ['Consumers'],
    }),
    projectAccess: build.query<ProjectAccess, number>({
      query: (id) => ({ url: `/access/consumers/${id}/access/`, method: 'get' }),
      providesTags: ['Connections'],
    }),
    requestableProjects: build.query<RequestableProject[], void>({
      query: () => ({ url: '/access/consumers/requestable/', method: 'get' }),
      providesTags: ['Consumers'],
    }),

    // --- Project access requests ---
    projectRequests: build.query<ProjectAccessRequest[], void>({
      query: () => ({ url: '/access/project-requests/', method: 'get' }),
      providesTags: ['GrantRequests'],
    }),
    createProjectRequest: build.mutation<
      ProjectAccessRequest,
      { consumer: number; message?: string }
    >({
      query: (body) => ({ url: '/access/project-requests/', method: 'post', data: body }),
      invalidatesTags: ['GrantRequests'],
    }),
    approveProjectRequest: build.mutation<ProjectAccessRequest, number>({
      query: (id) => ({ url: `/access/project-requests/${id}/approve/`, method: 'post' }),
      invalidatesTags: ['GrantRequests', 'Consumers'],
    }),
    denyProjectRequest: build.mutation<ProjectAccessRequest, number>({
      query: (id) => ({ url: `/access/project-requests/${id}/deny/`, method: 'post' }),
      invalidatesTags: ['GrantRequests'],
    }),

    // --- Audit ---
    audit: build.query<
      Paginated<AuditLog>,
      { page?: number; page_size?: number; status?: string; client_org?: number }
    >({
      query: (params) => ({ url: '/access/audit/', method: 'get', params }),
      providesTags: ['Audit'],
    }),

    // --- Interactive access (dev portal) ---
    previewData: build.mutation<
      Record<string, unknown>,
      { orgId: number; provider: string; accountId?: string; resource?: string }
    >({
      query: ({ orgId, provider, accountId, resource }) => ({
        url: `/access/clients/${orgId}/${provider}/data`,
        method: 'get',
        params: { ...(accountId ? { account_id: accountId } : {}), ...(resource ? { resource } : {}) },
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
  useCreateProjectMutation,
  useUpdateProjectMutation,
  useRotateKeyMutation,
  useProjectAccessQuery,
  useRequestableProjectsQuery,
  useProjectRequestsQuery,
  useCreateProjectRequestMutation,
  useApproveProjectRequestMutation,
  useDenyProjectRequestMutation,
  useAuditQuery,
  usePreviewDataMutation,
  useFetchTokenMutation,
  useRequestConnectionMutation,
} = accessApi
