import { apiSlice } from '@/app/api/apiSlice'
import type { Announcement, ConnectionRequest, Note } from '@/types'

export const portalApi = apiSlice.injectEndpoints({
  endpoints: (build) => ({
    announcements: build.query<Announcement[], void>({
      query: () => ({ url: '/portal/announcements/', method: 'get' }),
      providesTags: ['Announcements'],
    }),
    createAnnouncement: build.mutation<Announcement, Partial<Announcement>>({
      query: (body) => ({ url: '/portal/announcements/', method: 'post', data: body }),
      invalidatesTags: ['Announcements'],
    }),
    notes: build.query<Note[], number | void>({
      query: (clientOrg) => ({
        url: '/portal/notes/',
        method: 'get',
        params: clientOrg ? { client_org: clientOrg } : undefined,
      }),
      providesTags: ['Notes'],
    }),
    updateNote: build.mutation<Note, { id: number; status: string }>({
      query: ({ id, status }) => ({
        url: `/portal/notes/${id}/`,
        method: 'patch',
        data: { status },
      }),
      invalidatesTags: ['Notes'],
    }),
    requests: build.query<ConnectionRequest[], void>({
      query: () => ({ url: '/portal/connection-requests/', method: 'get' }),
      providesTags: ['Requests'],
    }),
    updateRequest: build.mutation<ConnectionRequest, { id: number; status: string }>({
      query: ({ id, status }) => ({
        url: `/portal/connection-requests/${id}/`,
        method: 'patch',
        data: { status },
      }),
      invalidatesTags: ['Requests'],
    }),
  }),
})

export const {
  useAnnouncementsQuery,
  useCreateAnnouncementMutation,
  useNotesQuery,
  useUpdateNoteMutation,
  useRequestsQuery,
  useUpdateRequestMutation,
} = portalApi
