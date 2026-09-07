import { apiSlice } from '@/app/api/apiSlice'
import type { User } from '@/types'

export const accountApi = apiSlice.injectEndpoints({
  endpoints: (build) => ({
    changePassword: build.mutation<
      { ok: boolean },
      { old_password: string; new_password: string }
    >({
      query: (body) => ({ url: '/auth/change-password/', method: 'post', data: body }),
    }),
    updateProfile: build.mutation<
      User,
      { first_name?: string; last_name?: string; email?: string }
    >({
      query: (body) => ({ url: '/auth/me/', method: 'patch', data: body }),
    }),
  }),
})

export const { useChangePasswordMutation, useUpdateProfileMutation } = accountApi
