import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from './layout/AppShell'
import { PageWrapper } from './layout/PageWrapper'
import Dashboard from './pages/Dashboard'
import Onboarding from './pages/Onboarding'
import CouncilStub from './pages/CouncilStub'
import ProgressStub from './pages/ProgressStub'
import SettingsStub from './pages/SettingsStub'
import CheckInStub from './pages/CheckInStub'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Onboarding renders without AppShell — full-screen experience */}
        <Route path="/onboarding" element={<Onboarding />} />

        {/* Main app routes with layout shell */}
        <Route
          path="*"
          element={
            <AppShell>
              <PageWrapper>
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/council" element={<CouncilStub />} />
                  <Route path="/progress" element={<ProgressStub />} />
                  <Route path="/settings" element={<SettingsStub />} />
                  <Route path="/checkin" element={<CheckInStub />} />
                </Routes>
              </PageWrapper>
            </AppShell>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}
