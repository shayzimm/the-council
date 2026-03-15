import { NavLink } from 'react-router-dom'

interface MobileDrawerProps {
  isOpen: boolean
  onClose: () => void
}

const navLinks = [
  { to: '/dashboard', label: 'Home' },
  { to: '/council', label: 'Council' },
  { to: '/progress', label: 'Progress' },
  { to: '/settings', label: 'Settings' },
]

export function MobileDrawer({ isOpen, onClose }: MobileDrawerProps) {
  return (
    <>
      {/* Backdrop */}
      <div
        role="presentation"
        onClick={onClose}
        className={[
          'fixed inset-0 z-40 bg-black/40 transition-opacity duration-300 md:hidden',
          isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none',
        ].join(' ')}
      />

      {/* Drawer panel */}
      <div
        inert={!isOpen || undefined}
        className={[
          'fixed top-0 left-0 h-full w-72 z-50 bg-aura-brown flex flex-col pt-16 px-8',
          'transition-transform duration-300 ease-in-out md:hidden',
          isOpen ? 'translate-x-0' : '-translate-x-full',
        ].join(' ')}
      >
        <nav>
          <ul className="flex flex-col gap-6 mt-4">
            {navLinks.map(({ to, label }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    [
                      'font-display text-2xl transition-colors',
                      isActive ? 'text-aura-gold' : 'text-aura-cream hover:text-aura-gold',
                    ].join(' ')
                  }
                >
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </>
  )
}
