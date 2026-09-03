import { createApi } from '@reduxjs/toolkit/query/react'

import { axiosBaseQuery } from './axiosBaseQuery'

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: axiosBaseQuery(),
  tagTypes: [
    'Providers',
    'Connections',
    'Consumers',
    'Grants',
    'Announcements',
    'Notes',
    'Requests',
    'Audit',
    'Orgs',
    'Users',
  ],
  endpoints: () => ({}),
})
