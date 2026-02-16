import { Route, Routes, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './hooks/useAuth'
import { CompanyProvider } from './hooks/useCompany'
import LoginPage from './pages/Login'
import DashboardPage from './pages/Dashboard'
import NumbersPage from './pages/Numbers'
import SchedulePage from './pages/Schedule'
import AdminUsersPage from './pages/AdminUsers'
import ProfilePage from './pages/Profile'
import BillingPage from './pages/Billing'
import CompanySelectorPage from './pages/CompanySelector'
import ScenariosPage from './pages/Scenarios'
import OutboundLinesPage from './pages/OutboundLines'

const App = () => {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        {/* Super admin routes */}
        <Route path="/admin/*" element={
          <ProtectedRoute requireSuperuser>
            <Layout>
              <Routes>
                <Route path="companies" element={<CompanySelectorPage />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        } />

        {/* Company-scoped routes */}
        <Route path="/:companySlug/*" element={
          <CompanyProvider>
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <Layout>
                <Routes>
                  <Route path="dashboard" element={<DashboardPage />} />
                  <Route path="numbers" element={<NumbersPage />} />
                  <Route path="schedule" element={<SchedulePage />} />
                  <Route path="billing" element={<BillingPage />} />
                  <Route path="admins" element={<AdminUsersPage />} />
                  <Route path="scenarios" element={<ScenariosPage />} />
                  <Route path="outbound-lines" element={<ProtectedRoute requireSuperuser><OutboundLinesPage /></ProtectedRoute>} />
                  <Route path="profile" element={<ProfilePage />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          </CompanyProvider>
        } />

        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
