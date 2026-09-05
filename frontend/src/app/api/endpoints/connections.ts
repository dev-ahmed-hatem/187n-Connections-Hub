import { apiSlice } from '@/app/api/apiSlice'
import type { ConnectionOverview } from '@/types'

export const connectionsApi = apiSlice.injectEndpoints({
  endpoints: (build) => ({
    overview: build.query<ConnectionOverview, number | void>({
      query: (clientOrg) => ({
        url: '/connections/overview/',
        method: 'get',
        params: clientOrg ? { client_org: clientOrg } : undefined,
      }),
      providesTags: ['Connections'],
    }),
    startConnection: build.mutation<
      { authorize_url: string },
      { provider: string; client_org?: number; params?: Record<string, string> }
    >({
      query: (body) => ({ url: '/connections/start/', method: 'post', data: body }),
    }),
    testConnection: build.mutation<{ ok: boolean; status: string }, number>({
      query: (id) => ({ url: `/connections/${id}/test`, method: 'post' }),
      invalidatesTags: ['Connections', 'Dashboard'],
    }),
  }),
})

export const {
  useOverviewQuery,
  useStartConnectionMutation,
  useTestConnectionMutation,
} = connectionsApi
