import { apiSlice } from '@/app/api/apiSlice'
import type { User } from '@/types'

interface LoginResponse {
  access: string
  refresh: string
  user: User
}

export const authApi = apiSlice.injectEndpoints({
  endpoints: (build) => ({
    login: build.mutation<LoginResponse, { username: string; password: string }>({
      query: (body) => ({ url: '/auth/login/', method: 'post', data: body }),
    }),
    me: build.query<User, void>({
      query: () => ({ url: '/auth/me/', method: 'get' }),
    }),
  }),
})

export const { useLoginMutation, useMeQuery } = authApi
