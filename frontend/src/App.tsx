import { Navigate, Route, Routes } from 'react-router-dom'

import ProtectedRoute from '@/app/routes/ProtectedRoute'
import RequireRole from '@/app/routes/RequireRole'
import LoginPage from '@/pages/auth/LoginPage'
import AccountPage from '@/pages/account/AccountPage'
import DashboardPage from '@/pages/dashboard/DashboardPage'
import ClientMessagesPage from '@/pages/staff/ClientMessagesPage'
import ClientConnectionsPage from '@/pages/client/ClientConnectionsPage'
import ClientUpdatesPage from '@/pages/client/ClientUpdatesPage'
import ProjectsPage from '@/pages/developer/ProjectsPage'
import QuickstartPage from '@/pages/developer/QuickstartPage'
import AdminApprovalsPage from '@/pages/admin/AdminApprovalsPage'
import AdminProjectsPage from '@/pages/admin/AdminProjectsPage'
import AdminOrgsPage from '@/pages/admin/AdminOrgsPage'
import AdminAnnouncementsPage from '@/pages/admin/AdminAnnouncementsPage'
import AdminAuditPage from '@/pages/admin/AdminAuditPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route index element={<DashboardPage />} />
        <Route path="account" element={<AccountPage />} />
        <Route path="staff/messages" element={
          <RequireRole roles={['developer']}><ClientMessagesPage /></RequireRole>} />

        <Route path="client/connections" element={
          <RequireRole roles={['client']}><ClientConnectionsPage /></RequireRole>} />
        <Route path="client/updates" element={
          <RequireRole roles={['client']}><ClientUpdatesPage /></RequireRole>} />

        <Route path="dev/projects" element={
          <RequireRole roles={['developer']}><ProjectsPage /></RequireRole>} />
        <Route path="dev/quickstart" element={
          <RequireRole roles={['developer']}><QuickstartPage /></RequireRole>} />

        <Route path="admin/approvals" element={
          <RequireRole roles={['admin']}><AdminApprovalsPage /></RequireRole>} />
        <Route path="admin/projects" element={
          <RequireRole roles={['admin']}><AdminProjectsPage /></RequireRole>} />
        <Route path="admin/orgs" element={
          <RequireRole roles={['admin']}><AdminOrgsPage /></RequireRole>} />
        <Route path="admin/announcements" element={
          <RequireRole roles={['admin']}><AdminAnnouncementsPage /></RequireRole>} />
        <Route path="admin/audit" element={
          <RequireRole roles={['admin']}><AdminAuditPage /></RequireRole>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
