import { apiSlice } from '@/app/api/apiSlice'
import type { DashboardSummary } from '@/types'

export const dashboardApi = apiSlice.injectEndpoints({
  endpoints: (build) => ({
    dashboard: build.query<DashboardSummary, void>({
      query: () => ({ url: '/dashboard/', method: 'get' }),
      providesTags: ['Dashboard'],
    }),
  }),
})

export const { useDashboardQuery } = dashboardApi
