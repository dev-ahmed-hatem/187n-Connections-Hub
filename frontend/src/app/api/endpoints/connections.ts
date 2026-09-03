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
      { provider: string; client_org?: number }
    >({
      query: (body) => ({ url: '/connections/start/', method: 'post', data: body }),
    }),
  }),
})

export const { useOverviewQuery, useStartConnectionMutation } = connectionsApi
