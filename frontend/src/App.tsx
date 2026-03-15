import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from './layout/AppShell'
import { PageWrapper } from './layout/PageWrapper'
import Dashboard from './pages/Dashboard'
import CouncilStub from './pages/CouncilStub'
import ProgressStub from './pages/ProgressStub'
import SettingsStub from './pages/SettingsStub'
import CheckInStub from './pages/CheckInStub'

export default function App() {
  return (
    <BrowserRouter>
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
    </BrowserRouter>
  )
}
