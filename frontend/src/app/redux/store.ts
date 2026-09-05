import { configureStore } from '@reduxjs/toolkit'

import { apiSlice } from '@/app/api/apiSlice'
import authReducer from '@/app/slices/authSlice'
import uiReducer from '@/app/slices/uiSlice'

export const store = configureStore({
  reducer: {
    [apiSlice.reducerPath]: apiSlice.reducer,
    auth: authReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(apiSlice.middleware),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
