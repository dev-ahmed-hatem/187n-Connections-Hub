import { createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'

interface UiState {
  dark: boolean
}

const initialState: UiState = {
  dark: localStorage.getItem('theme') !== 'light',
}

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleTheme(state) {
      state.dark = !state.dark
      localStorage.setItem('theme', state.dark ? 'dark' : 'light')
    },
    setTheme(state, action: PayloadAction<boolean>) {
      state.dark = action.payload
      localStorage.setItem('theme', action.payload ? 'dark' : 'light')
    },
  },
})

export const { toggleTheme, setTheme } = uiSlice.actions
export default uiSlice.reducer
