import { Navigate, Route, Routes } from 'react-router-dom'

import ProtectedRoute from '@/app/routes/ProtectedRoute'
import RequireRole from '@/app/routes/RequireRole'
import { useAppSelector } from '@/app/redux/hooks'
import LoginPage from '@/pages/auth/LoginPage'
import ClientConnectionsPage from '@/pages/client/ClientConnectionsPage'
import ClientUpdatesPage from '@/pages/client/ClientUpdatesPage'
import DevAccessPage from '@/pages/developer/DevAccessPage'
import DevConsumersPage from '@/pages/developer/DevConsumersPage'
import AdminGrantsPage from '@/pages/admin/AdminGrantsPage'
import AdminOrgsPage from '@/pages/admin/AdminOrgsPage'
import AdminAnnouncementsPage from '@/pages/admin/AdminAnnouncementsPage'
import AdminAuditPage from '@/pages/admin/AdminAuditPage'

function HomeRedirect() {
  const user = useAppSelector((s) => s.auth.user)
  if (!user) return <Navigate to="/login" replace />
  if (user.role === 'client') return <Navigate to="/client/connections" replace />
  if (user.role === 'developer') return <Navigate to="/dev/access" replace />
  return <Navigate to="/admin/grants" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route index element={<HomeRedirect />} />

        <Route
          path="client/connections"
          element={
            <RequireRole roles={['client']}>
              <ClientConnectionsPage />
            </RequireRole>
          }
        />
        <Route
          path="client/updates"
          element={
            <RequireRole roles={['client']}>
              <ClientUpdatesPage />
            </RequireRole>
          }
        />

        <Route
          path="dev/access"
          element={
            <RequireRole roles={['developer']}>
              <DevAccessPage />
            </RequireRole>
          }
        />
        <Route
          path="dev/consumers"
          element={
            <RequireRole roles={['developer']}>
              <DevConsumersPage />
            </RequireRole>
          }
        />

        <Route
          path="admin/grants"
          element={
            <RequireRole roles={['admin']}>
              <AdminGrantsPage />
            </RequireRole>
          }
        />
        <Route
          path="admin/orgs"
          element={
            <RequireRole roles={['admin']}>
              <AdminOrgsPage />
            </RequireRole>
          }
        />
        <Route
          path="admin/announcements"
          element={
            <RequireRole roles={['admin']}>
              <AdminAnnouncementsPage />
            </RequireRole>
          }
        />
        <Route
          path="admin/audit"
          element={
            <RequireRole roles={['admin']}>
              <AdminAuditPage />
            </RequireRole>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
