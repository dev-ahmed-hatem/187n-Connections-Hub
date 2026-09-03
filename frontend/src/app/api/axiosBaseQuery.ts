import axios from 'axios'
import type { AxiosError, AxiosRequestConfig } from 'axios'
import type { BaseQueryFn } from '@reduxjs/toolkit/query'

const API_BASE = import.meta.env.VITE_API_BASE_URL as string

export const httpClient = axios.create({ baseURL: API_BASE })

// Attach the JWT access token to every request.
httpClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access')
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On 401, try a one-shot refresh against /auth/refresh/, then replay.
httpClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as AxiosRequestConfig & { _retry?: boolean }
    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh')
      if (refresh) {
        try {
          const res = await axios.post(`${API_BASE}/auth/refresh/`, { refresh })
          const newAccess = res.data.access as string
          localStorage.setItem('access', newAccess)
          original.headers = original.headers ?? {}
          ;(original.headers as Record<string, string>).Authorization = `Bearer ${newAccess}`
          return httpClient(original)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      } else {
        localStorage.clear()
      }
    }
    return Promise.reject(error)
  },
)

export interface AxiosBaseQueryArgs {
  url: string
  method?: AxiosRequestConfig['method']
  data?: unknown
  params?: unknown
}

export const axiosBaseQuery =
  (): BaseQueryFn<AxiosBaseQueryArgs, unknown, unknown> =>
  async ({ url, method = 'get', data, params }) => {
    try {
      const result = await httpClient({ url, method, data, params })
      return { data: result.data }
    } catch (axiosError) {
      const err = axiosError as AxiosError
      return {
        error: {
          status: err.response?.status,
          data: err.response?.data || err.message,
        },
      }
    }
  }
