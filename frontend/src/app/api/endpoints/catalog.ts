import { apiSlice } from '@/app/api/apiSlice'
import type { ClientOrg, Provider } from '@/types'

export const catalogApi = apiSlice.injectEndpoints({
  endpoints: (build) => ({
    providers: build.query<Provider[], void>({
      query: () => ({ url: '/providers/', method: 'get' }),
      providesTags: ['Providers'],
    }),
    orgs: build.query<ClientOrg[], void>({
      query: () => ({ url: '/users/orgs/', method: 'get' }),
      providesTags: ['Orgs'],
    }),
    createOrg: build.mutation<ClientOrg, { name: string; slug: string; notes?: string }>({
      query: (body) => ({ url: '/users/orgs/', method: 'post', data: body }),
      invalidatesTags: ['Orgs'],
    }),
  }),
})

export const { useProvidersQuery, useOrgsQuery, useCreateOrgMutation } = catalogApi
