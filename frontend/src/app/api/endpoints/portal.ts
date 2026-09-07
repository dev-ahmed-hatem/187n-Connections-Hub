import { apiSlice } from '@/app/api/apiSlice'
import type {
  Announcement,
  Comment,
  ConnectionRequest,
  Note,
  Notification,
} from '@/types'

export const portalApi = apiSlice.injectEndpoints({
  endpoints: (build) => ({
    announcements: build.query<Announcement[], void>({
      query: () => ({ url: '/portal/announcements/', method: 'get' }),
      providesTags: ['Announcements'],
    }),
    createAnnouncement: build.mutation<Announcement, Partial<Announcement>>({
      query: (body) => ({ url: '/portal/announcements/', method: 'post', data: body }),
      invalidatesTags: ['Announcements', 'Notifications'],
    }),

    notes: build.query<Note[], number | void>({
      query: (clientOrg) => ({
        url: '/portal/notes/',
        method: 'get',
        params: clientOrg ? { client_org: clientOrg } : undefined,
      }),
      providesTags: ['Notes'],
    }),
    createNote: build.mutation<
      Note,
      { client_org: number; type: string; title: string; body?: string }
    >({
      query: (body) => ({ url: '/portal/notes/', method: 'post', data: body }),
      invalidatesTags: ['Notes', 'Notifications'],
    }),
    resolveNote: build.mutation<Note, number>({
      query: (id) => ({ url: `/portal/notes/${id}/resolve/`, method: 'post' }),
      invalidatesTags: ['Notes', 'Notifications'],
    }),
    reopenNote: build.mutation<Note, number>({
      query: (id) => ({ url: `/portal/notes/${id}/reopen/`, method: 'post' }),
      invalidatesTags: ['Notes', 'Notifications'],
    }),

    comments: build.query<Comment[], number>({
      query: (noteId) => ({ url: '/portal/comments/', method: 'get', params: { note: noteId } }),
      providesTags: ['Comments'],
    }),
    createComment: build.mutation<Comment, { note: number; body: string }>({
      query: (body) => ({ url: '/portal/comments/', method: 'post', data: body }),
      invalidatesTags: ['Comments', 'Notifications'],
    }),

    notifications: build.query<Notification[], void>({
      query: () => ({ url: '/portal/notifications/', method: 'get' }),
      providesTags: ['Notifications'],
    }),
    unreadCount: build.query<{ count: number }, void>({
      query: () => ({ url: '/portal/notifications/unread-count/', method: 'get' }),
      providesTags: ['Notifications'],
    }),
    markNotificationRead: build.mutation<{ ok: boolean }, number>({
      query: (id) => ({ url: `/portal/notifications/${id}/read/`, method: 'post' }),
      invalidatesTags: ['Notifications'],
    }),
    markAllNotificationsRead: build.mutation<{ ok: boolean }, void>({
      query: () => ({ url: '/portal/notifications/mark-all-read/', method: 'post' }),
      invalidatesTags: ['Notifications'],
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
      invalidatesTags: ['Requests', 'Notifications'],
    }),
  }),
})

export const {
  useAnnouncementsQuery,
  useCreateAnnouncementMutation,
  useNotesQuery,
  useCreateNoteMutation,
  useResolveNoteMutation,
  useReopenNoteMutation,
  useCommentsQuery,
  useCreateCommentMutation,
  useNotificationsQuery,
  useUnreadCountQuery,
  useMarkNotificationReadMutation,
  useMarkAllNotificationsReadMutation,
  useRequestsQuery,
  useUpdateRequestMutation,
} = portalApi
