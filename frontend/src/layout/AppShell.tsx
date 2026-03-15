import { useState } from 'react'
import { TopNav } from './TopNav'
import { MobileDrawer } from './MobileDrawer'

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const [drawerOpen, setDrawerOpen] = useState(false)

  return (
    <div className="min-h-screen bg-aura-cream">
      <TopNav onHamburgerClick={() => setDrawerOpen(true)} />
      <MobileDrawer isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />
      {/* Offset for fixed nav bar */}
      <div className="pt-14">{children}</div>
    </div>
  )
}
