import { NavLink } from 'react-router-dom'

interface TopNavProps {
  onHamburgerClick: () => void
}

const navLinks = [
  { to: '/dashboard', label: 'Home' },
  { to: '/council', label: 'Council' },
  { to: '/progress', label: 'Progress' },
]

export function TopNav({ onHamburgerClick }: TopNavProps) {
  return (
    <nav className="fixed top-0 inset-x-0 z-30 bg-aura-white border-b border-aura-surface">
      <div className="max-w-screen-lg mx-auto px-4 h-14 flex items-center justify-between">
        {/* Wordmark */}
        <span className="font-display text-aura-gold tracking-[0.2em] text-lg select-none">
          AURA
        </span>

        {/* Desktop nav links */}
        <ul className="hidden md:flex items-center gap-8">
          {navLinks.map(({ to, label }) => (
            <li key={to}>
              <NavLink
                to={to}
                className={({ isActive }) =>
                  [
                    'font-body text-sm transition-colors',
                    isActive
                      ? 'text-aura-brown border-b border-aura-blush pb-0.5'
                      : 'text-aura-muted hover:text-aura-brown',
                  ].join(' ')
                }
              >
                {label}
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Mobile hamburger */}
        <button
          aria-label="Open menu"
          onClick={onHamburgerClick}
          className="md:hidden text-aura-brown p-2 -mr-2"
        >
          <svg aria-hidden="true" width="22" height="22" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
            <line x1="2" y1="5.5" x2="20" y2="5.5" />
            <line x1="2" y1="11" x2="20" y2="11" />
            <line x1="2" y1="16.5" x2="20" y2="16.5" />
          </svg>
        </button>
      </div>
    </nav>
  )
}
