import { apiSlice } from '@/app/api/apiSlice'
import type { User } from '@/types'

export const adminApi = apiSlice.injectEndpoints({
  endpoints: (build) => ({
    users: build.query<User[], void>({
      query: () => ({ url: '/users/accounts/', method: 'get' }),
      providesTags: ['Users'],
    }),
    createUser: build.mutation<
      User,
      {
        username: string
        password: string
        role: string
        email?: string
        client_org?: number | null
      }
    >({
      query: (body) => ({ url: '/users/accounts/', method: 'post', data: body }),
      invalidatesTags: ['Users'],
    }),
    deleteUser: build.mutation<void, number>({
      query: (id) => ({ url: `/users/accounts/${id}/`, method: 'delete' }),
      invalidatesTags: ['Users'],
    }),
  }),
})

export const { useUsersQuery, useCreateUserMutation, useDeleteUserMutation } = adminApi
