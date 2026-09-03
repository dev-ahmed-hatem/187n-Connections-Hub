import { createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

import type { User } from '@/types'

interface AuthState {
  user: User | null
  access: string | null
  refresh: string | null
}

const initialState: AuthState = {
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  access: localStorage.getItem('access'),
  refresh: localStorage.getItem('refresh'),
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials(
      state,
      action: PayloadAction<{ user: User; access: string; refresh: string }>,
    ) {
      const { user, access, refresh } = action.payload
      state.user = user
      state.access = access
      state.refresh = refresh
      localStorage.setItem('user', JSON.stringify(user))
      localStorage.setItem('access', access)
      localStorage.setItem('refresh', refresh)
    },
    setUser(state, action: PayloadAction<User>) {
      state.user = action.payload
      localStorage.setItem('user', JSON.stringify(action.payload))
    },
    logout(state) {
      state.user = null
      state.access = null
      state.refresh = null
      localStorage.removeItem('user')
      localStorage.removeItem('access')
      localStorage.removeItem('refresh')
    },
  },
})

export const { setCredentials, setUser, logout } = authSlice.actions
export default authSlice.reducer
