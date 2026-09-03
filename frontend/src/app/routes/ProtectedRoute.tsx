import { Navigate, Outlet } from 'react-router-dom'

import { useAppSelector } from '@/app/redux/hooks'
import AppLayout from '@/components/AppLayout'

export default function ProtectedRoute() {
  const user = useAppSelector((s) => s.auth.user)
  if (!user) return <Navigate to="/login" replace />
  return (
    <AppLayout>
      <Outlet />
    </AppLayout>
  )
}
