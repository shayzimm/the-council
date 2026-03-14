# Aura Scaffold & Brand Shell Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the full Aura project structure — Vite/React/TypeScript frontend with brand design system, FastAPI/SQLite backend, responsive layout shell, and static dashboard skeleton.

**Architecture:** The frontend is a Vite + React SPA with brand tokens baked into Tailwind config, a responsive AppShell (top nav desktop / hamburger drawer mobile), and a static dashboard. The backend is a minimal FastAPI app with CORS and a health endpoint. No live data — everything on the dashboard is static placeholder content.

**Tech Stack:** Vite 5, React 18, TypeScript, Tailwind CSS 3, React Router v6, Vitest, React Testing Library (frontend) · FastAPI, SQLAlchemy 2, Pydantic v2, pytest, httpx (backend)

---

## Chunk 1: Backend Scaffold

### Task 1: Backend dependencies and project structure

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/database.py`
- Create: `backend/models/__init__.py`
- Create: `backend/routes/__init__.py`
- Create: `backend/routes/health.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Create `backend/requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
pydantic==2.9.2
python-dotenv==1.0.1
pytest==8.3.3
httpx==0.27.2
```

- [ ] **Step 2: Create the backend directory structure**

```bash
mkdir -p backend/models backend/routes backend/tests
touch backend/models/__init__.py backend/routes/__init__.py backend/tests/__init__.py
```

- [ ] **Step 3: Write the failing health test**

`backend/tests/test_health.py`:
```python
import pytest
from fastapi.testclient import TestClient


def test_health_returns_ok():
    from main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "aura"}
```

- [ ] **Step 4: Create a virtual environment, install dependencies, and run test to verify it fails**

```bash
cd backend
python -m venv .venv
# Windows (Git Bash):
source .venv/Scripts/activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/test_health.py -v
```

The virtual environment keeps backend dependencies isolated from the global Python install. Activate it (`source .venv/Scripts/activate`) at the start of every backend terminal session.

Expected: `FAILED` — `ModuleNotFoundError: No module named 'main'`

Expected: `FAILED` — `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 5: Create `backend/routes/health.py`**

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "app": "aura"}
```

- [ ] **Step 6: Create `backend/database.py`**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./aura.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 7: Create `backend/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.health import router as health_router

app = FastAPI(title="Aura API")

# Dev-only CORS: allow Vite dev server.
# Make this env-variable-driven before any deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
```

- [ ] **Step 8: Run test to verify it passes**

```bash
cd backend
python -m pytest tests/test_health.py -v
```

Expected: `PASSED`

- [ ] **Step 9: Smoke-test the running server**

```bash
cd backend
uvicorn main:app --reload
# In a second terminal:
curl http://localhost:8000/health
```

Expected: `{"status":"ok","app":"aura"}`

- [ ] **Step 10: Commit**

```bash
git add backend/
git commit -m "feat: scaffold FastAPI backend with health endpoint"
```

---

## Chunk 2: Frontend Project Setup

### Task 2: Scaffold Vite + React + TypeScript project

**Files:**
- Run: `npm create vite@latest frontend -- --template react-ts`
- Modify: `frontend/index.html`
- Modify: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Modify: `frontend/src/styles/globals.css` (rename from `index.css`)
- Create: `frontend/src/vite-env.d.ts` (already exists after scaffold, verify)
- Create: `frontend/.env.example`
- Delete: `frontend/src/App.css`, `frontend/src/assets/react.svg`, `frontend/public/vite.svg`

- [ ] **Step 1: Scaffold the Vite project**

From the `aura/` root directory:
```bash
npm create vite@latest frontend -- --template react-ts
```

- [ ] **Step 2: Install dependencies**

```bash
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p --ts
npm install react-router-dom
npm install -D vitest @vitest/coverage-v8 jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

- [ ] **Step 3: Remove Vite boilerplate files**

```bash
rm frontend/src/App.css
rm frontend/src/assets/react.svg
rm frontend/public/vite.svg
```

- [ ] **Step 4: Update `frontend/tailwind.config.ts` with brand tokens**

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'aura-cream': '#FAF7F2',
        'aura-surface': '#EDE8E0',
        'aura-blush': '#D4A89A',
        'aura-brown': '#2C2420',
        'aura-muted': '#8C7B74',
        'aura-gold': '#C9A96E',
        'aura-white': '#FFFDF9',
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', 'serif'],
        body: ['"DM Sans"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config
```

- [ ] **Step 5: Create `frontend/src/styles/globals.css`**

Delete the default `src/index.css` and create `src/styles/globals.css`:

```bash
rm frontend/src/index.css
```

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-aura-cream text-aura-brown font-body;
  }
}
```

- [ ] **Step 6: Update `frontend/index.html` with Google Fonts and correct CSS path**

Replace the entire contents of `frontend/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Aura</title>
    <!-- Google Fonts: loaded via <link> to avoid render-blocking FOUT -->
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&display=swap"
      rel="stylesheet"
    />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 7: Update `frontend/vite.config.ts` to add Vitest config**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test-setup.ts',
  },
})
```

- [ ] **Step 8: Create `frontend/src/test-setup.ts`**

```typescript
import '@testing-library/jest-dom'
```

- [ ] **Step 9: Update `frontend/tsconfig.json` to include Vitest globals**

Open `frontend/tsconfig.json`. Add `"types": ["vitest/globals"]` inside `compilerOptions`:

```json
{
  "compilerOptions": {
    "types": ["vitest/globals"]
  }
}
```

Merge this into the existing `compilerOptions` — do not replace the entire file.

- [ ] **Step 10: Create `frontend/.env.example`**

```
# Backend API base URL
VITE_API_URL=http://localhost:8000
```

- [ ] **Step 11: Create `frontend/src/types/index.ts` stub**

```typescript
// Shared TypeScript interfaces for Aura.
// Add domain types here as sub-projects are implemented.

export {}
```

- [ ] **Step 12: Create `frontend/src/hooks/.gitkeep`**

```bash
touch frontend/src/hooks/.gitkeep
```

- [ ] **Step 13: Write a failing smoke test to verify Tailwind tokens are configured**

Create `frontend/src/styles/tokens.test.ts`:

```typescript
// Verifies brand token names are correct strings (not a runtime test —
// this catches typos in the token names used in component classNames).
describe('brand token names', () => {
  const tokens = [
    'aura-cream',
    'aura-surface',
    'aura-blush',
    'aura-brown',
    'aura-muted',
    'aura-gold',
    'aura-white',
  ]

  it('all expected tokens are defined', () => {
    tokens.forEach((token) => {
      expect(typeof token).toBe('string')
      expect(token.startsWith('aura-')).toBe(true)
    })
  })
})
```

- [ ] **Step 14: Run test to verify it passes**

```bash
cd frontend
npx vitest run src/styles/tokens.test.ts
```

Expected: `PASS` — 1 test passed

- [ ] **Step 15: Verify dev server starts and shows blank page on brand background**

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`. The page should be blank (we'll clear `src/main.tsx` content shortly) with a warm cream background — not white. If it's white, the globals.css import is missing.

- [ ] **Step 16: Commit**

```bash
cd ..
git add frontend/
git commit -m "feat: scaffold Vite/React/TS frontend with Tailwind brand tokens"
```

---

## Chunk 3: Layout Shell

### Task 3: Shared types and layout components

**Files:**
- Modify: `frontend/src/types/index.ts`
- Create: `frontend/src/layout/AppShell.tsx`
- Create: `frontend/src/layout/TopNav.tsx`
- Create: `frontend/src/layout/MobileDrawer.tsx`
- Create: `frontend/src/layout/PageWrapper.tsx`
- Create: `frontend/src/layout/TopNav.test.tsx`
- Create: `frontend/src/layout/MobileDrawer.test.tsx`
- Create: `frontend/src/layout/PageWrapper.test.tsx`
- Modify: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/pages/CouncilStub.tsx`
- Create: `frontend/src/pages/ProgressStub.tsx`
- Create: `frontend/src/pages/SettingsStub.tsx`
- Create: `frontend/src/pages/CheckInStub.tsx`

---

#### Task 3a: PageWrapper

- [ ] **Step 1: Write failing test for PageWrapper**

`frontend/src/layout/PageWrapper.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react'
import { PageWrapper } from './PageWrapper'

describe('PageWrapper', () => {
  it('renders children', () => {
    render(<PageWrapper><p>hello</p></PageWrapper>)
    expect(screen.getByText('hello')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend
npx vitest run src/layout/PageWrapper.test.tsx
```

Expected: `FAILED` — cannot find module `./PageWrapper`

- [ ] **Step 3: Create `frontend/src/layout/PageWrapper.tsx`**

```tsx
interface PageWrapperProps {
  children: React.ReactNode
}

export function PageWrapper({ children }: PageWrapperProps) {
  return (
    <main className="max-w-screen-lg mx-auto px-4 py-8 w-full">
      {children}
    </main>
  )
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run src/layout/PageWrapper.test.tsx
```

Expected: `PASS`

---

#### Task 3b: TopNav

- [ ] **Step 5: Write failing test for TopNav**

`frontend/src/layout/TopNav.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { TopNav } from './TopNav'

const renderTopNav = (onHamburgerClick = () => {}) =>
  render(
    <MemoryRouter>
      <TopNav onHamburgerClick={onHamburgerClick} />
    </MemoryRouter>
  )

describe('TopNav', () => {
  it('renders the AURA wordmark', () => {
    renderTopNav()
    expect(screen.getByText('AURA')).toBeInTheDocument()
  })

  it('renders desktop nav links', () => {
    renderTopNav()
    expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Council' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Progress' })).toBeInTheDocument()
  })

  it('calls onHamburgerClick when hamburger button is pressed', async () => {
    const handler = vi.fn()
    renderTopNav(handler)
    screen.getByRole('button', { name: /menu/i }).click()
    expect(handler).toHaveBeenCalledTimes(1)
  })
})
```

- [ ] **Step 6: Run test to verify it fails**

```bash
npx vitest run src/layout/TopNav.test.tsx
```

Expected: `FAILED` — cannot find module `./TopNav`

- [ ] **Step 7: Create `frontend/src/layout/TopNav.tsx`**

```tsx
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
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
            <line x1="2" y1="5.5" x2="20" y2="5.5" />
            <line x1="2" y1="11" x2="20" y2="11" />
            <line x1="2" y1="16.5" x2="20" y2="16.5" />
          </svg>
        </button>
      </div>
    </nav>
  )
}
```

- [ ] **Step 8: Run test to verify it passes**

```bash
npx vitest run src/layout/TopNav.test.tsx
```

Expected: `PASS` — 3 tests passed

---

#### Task 3c: MobileDrawer

- [ ] **Step 9: Write failing test for MobileDrawer**

`frontend/src/layout/MobileDrawer.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { MobileDrawer } from './MobileDrawer'

const renderDrawer = (isOpen: boolean, onClose = () => {}) =>
  render(
    <MemoryRouter>
      <MobileDrawer isOpen={isOpen} onClose={onClose} />
    </MemoryRouter>
  )

describe('MobileDrawer', () => {
  it('does not show nav links when closed', () => {
    renderDrawer(false)
    expect(screen.queryByRole('link', { name: 'Home' })).not.toBeVisible()
  })

  it('shows nav links when open', () => {
    renderDrawer(true)
    expect(screen.getByRole('link', { name: 'Home' })).toBeVisible()
    expect(screen.getByRole('link', { name: 'Council' })).toBeVisible()
  })

  it('calls onClose when backdrop is clicked', async () => {
    const handler = vi.fn()
    renderDrawer(true, handler)
    await userEvent.click(screen.getByRole('presentation'))
    expect(handler).toHaveBeenCalledTimes(1)
  })
})
```

- [ ] **Step 10: Run test to verify it fails**

```bash
npx vitest run src/layout/MobileDrawer.test.tsx
```

Expected: `FAILED` — cannot find module `./MobileDrawer`

- [ ] **Step 11: Create `frontend/src/layout/MobileDrawer.tsx`**

```tsx
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
```

- [ ] **Step 12: Run test to verify it passes**

```bash
npx vitest run src/layout/MobileDrawer.test.tsx
```

Expected: `PASS` — 3 tests passed

---

#### Task 3d: AppShell, App, routing, and stub pages

- [ ] **Step 13: Create `frontend/src/layout/AppShell.tsx`**

```tsx
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
```

- [ ] **Step 14: Create stub pages**

`frontend/src/pages/CouncilStub.tsx`:
```tsx
export default function CouncilStub() {
  return (
    <div className="py-16 text-center">
      <p className="font-display text-2xl text-aura-muted">Council — coming soon</p>
    </div>
  )
}
```

`frontend/src/pages/ProgressStub.tsx`:
```tsx
export default function ProgressStub() {
  return (
    <div className="py-16 text-center">
      <p className="font-display text-2xl text-aura-muted">Progress — coming soon</p>
    </div>
  )
}
```

`frontend/src/pages/SettingsStub.tsx`:
```tsx
export default function SettingsStub() {
  return (
    <div className="py-16 text-center">
      <p className="font-display text-2xl text-aura-muted">Settings — coming soon</p>
    </div>
  )
}
```

`frontend/src/pages/CheckInStub.tsx`:
```tsx
export default function CheckInStub() {
  return (
    <div className="py-16 text-center">
      <p className="font-display text-2xl text-aura-muted">Check-in — coming soon</p>
    </div>
  )
}
```

- [ ] **Step 15: Create `frontend/src/App.tsx`**

```tsx
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
```

- [ ] **Step 16: Update `frontend/src/main.tsx`**

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/globals.css'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)
```

Note: `Dashboard` import in `App.tsx` will fail until Task 4 creates it. Create a temporary stub at `frontend/src/pages/Dashboard.tsx` now:

```tsx
export default function Dashboard() {
  return <div />
}
```

- [ ] **Step 17: Verify app renders in browser**

```bash
cd frontend && npm run dev
```

Open `http://localhost:5173`. Expected:
- Cream background
- Top nav with "AURA" in gold
- Desktop: nav links on the right
- Mobile: hamburger icon; tapping it opens the dark drawer with Cormorant Garamond nav links

- [ ] **Step 18: Run all layout tests**

```bash
npx vitest run src/layout/
```

Expected: all tests pass

- [ ] **Step 19: Commit**

```bash
cd ..
git add frontend/src/layout/ frontend/src/App.tsx frontend/src/main.tsx frontend/src/pages/
git commit -m "feat: add responsive layout shell with top nav and mobile drawer"
```

---

## Chunk 4: Dashboard Page

### Task 4: Shared components and dashboard

**Files:**
- Create: `frontend/src/components/StatPill.tsx`
- Create: `frontend/src/components/StatPill.test.tsx`
- Create: `frontend/src/components/StreakChip.tsx`
- Create: `frontend/src/components/StreakChip.test.tsx`
- Replace: `frontend/src/pages/Dashboard.tsx`
- Create: `frontend/src/pages/Dashboard.test.tsx`

---

#### Task 4a: StatPill component

- [ ] **Step 1: Write failing test**

`frontend/src/components/StatPill.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react'
import { StatPill } from './StatPill'

describe('StatPill', () => {
  it('renders value and label', () => {
    render(<StatPill label="Recovery" value={74} unit="%" />)
    expect(screen.getByText('74%')).toBeInTheDocument()
    expect(screen.getByText('Recovery')).toBeInTheDocument()
  })

  it('renders without a unit', () => {
    render(<StatPill label="HRV" value="62ms" />)
    expect(screen.getByText('62ms')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npx vitest run src/components/StatPill.test.tsx
```

Expected: `FAILED`

- [ ] **Step 3: Create `frontend/src/components/StatPill.tsx`**

```tsx
interface StatPillProps {
  label: string
  value: string | number
  unit?: string
}

export function StatPill({ label, value, unit }: StatPillProps) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className="font-display text-xl text-aura-brown font-semibold leading-none">
        {value}{unit}
      </span>
      <span className="font-body text-xs text-aura-muted uppercase tracking-wider">
        {label}
      </span>
    </div>
  )
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npx vitest run src/components/StatPill.test.tsx
```

Expected: `PASS`

---

#### Task 4b: StreakChip component

- [ ] **Step 5: Write failing test**

`frontend/src/components/StreakChip.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react'
import { StreakChip } from './StreakChip'

describe('StreakChip', () => {
  it('renders habit label and day count', () => {
    render(<StreakChip label="Training" days={12} />)
    expect(screen.getByText('Training')).toBeInTheDocument()
    expect(screen.getByText('12d')).toBeInTheDocument()
  })
})
```

- [ ] **Step 6: Run test to verify it fails**

```bash
npx vitest run src/components/StreakChip.test.tsx
```

Expected: `FAILED`

- [ ] **Step 7: Create `frontend/src/components/StreakChip.tsx`**

```tsx
interface StreakChipProps {
  label: string
  days: number
}

export function StreakChip({ label, days }: StreakChipProps) {
  return (
    <div className="inline-flex items-center gap-1.5 bg-aura-surface rounded-full px-3 py-1.5">
      <span className="font-body text-sm text-aura-brown">{label}</span>
      <span className="font-body text-sm text-aura-gold font-medium">{days}d</span>
    </div>
  )
}
```

- [ ] **Step 8: Run test to verify it passes**

```bash
npx vitest run src/components/StreakChip.test.tsx
```

Expected: `PASS`

---

#### Task 4c: Dashboard page

- [ ] **Step 9: Write failing tests for Dashboard**

`frontend/src/pages/Dashboard.test.tsx`:
```tsx
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from './Dashboard'

const renderDashboard = () =>
  render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>
  )

describe('Dashboard', () => {
  it('renders the greeting', () => {
    renderDashboard()
    expect(screen.getByText(/Good morning, Shay/i)).toBeInTheDocument()
  })

  it('renders the check-in prompt', () => {
    renderDashboard()
    expect(screen.getByText(/Morning check-in/i)).toBeInTheDocument()
  })

  it('renders Whoop snapshot section', () => {
    renderDashboard()
    expect(screen.getByText('Recovery')).toBeInTheDocument()
    expect(screen.getByText('HRV')).toBeInTheDocument()
    expect(screen.getByText('Sleep')).toBeInTheDocument()
  })

  it('renders today\'s tasks', () => {
    renderDashboard()
    expect(screen.getByText(/Upper body/i)).toBeInTheDocument()
    expect(screen.getByText(/Tret night/i)).toBeInTheDocument()
    expect(screen.getByText(/NSDR/i)).toBeInTheDocument()
  })

  it('renders active streaks', () => {
    renderDashboard()
    expect(screen.getByText('Training')).toBeInTheDocument()
  })

  it('renders quick access links to Council', () => {
    renderDashboard()
    expect(screen.getAllByRole('link', { name: /Rex|Sage|Celeste|Council/i }).length).toBeGreaterThan(0)
  })

  it('renders this week at a glance section', () => {
    renderDashboard()
    expect(screen.getByText(/this week/i)).toBeInTheDocument()
  })
})
```

- [ ] **Step 10: Run tests to verify they fail**

```bash
npx vitest run src/pages/Dashboard.test.tsx
```

Expected: `FAILED` — dashboard is currently an empty stub

- [ ] **Step 11: Replace `frontend/src/pages/Dashboard.tsx` with full implementation**

```tsx
import { Link } from 'react-router-dom'
import { StatPill } from '../components/StatPill'
import { StreakChip } from '../components/StreakChip'

const today = new Date().toLocaleDateString('en-AU', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
})

// Static placeholder data — replaced with live data in a future sub-project
const WHOOP = { recovery: 74, hrv: '62ms', sleep: 87 }

const TASKS = [
  { label: 'Upper body — moderate intensity', agent: 'Rex' },
  { label: 'Tret night', agent: 'Celeste' },
  { label: '10 min NSDR', agent: 'Sage' },
]

const STREAKS = [
  { label: 'Training', days: 12 },
  { label: 'Skincare', days: 6 },
  { label: 'Check-ins', days: 3 },
]

const QUICK_ACCESS = [
  { label: 'Rex', to: '/council' },
  { label: 'Celeste', to: '/council' },
  { label: 'Sage', to: '/council' },
  { label: 'The Council', to: '/council' },
]

export default function Dashboard() {
  return (
    <div className="flex flex-col gap-6">

      {/* Greeting */}
      <div>
        <h1 className="font-display text-3xl text-aura-brown">Good morning, Shay</h1>
        <p className="font-body text-sm text-aura-muted mt-1">{today}</p>
        <p className="font-body text-sm text-aura-muted italic mt-0.5">
          Rest is as productive as effort.
        </p>
      </div>

      {/* Check-in prompt */}
      <Link
        to="/checkin"
        className="block border-l-[3px] border-aura-blush pl-4 py-3 hover:bg-aura-surface/50 rounded-r-lg transition-colors"
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="font-body text-sm font-medium text-aura-brown">Morning check-in</p>
            <p className="font-body text-xs text-aura-muted">~2 minutes</p>
          </div>
          <span className="text-aura-blush text-lg">→</span>
        </div>
      </Link>

      {/* Whoop snapshot */}
      <div className="border-l-[3px] border-aura-gold pl-4 py-3">
        <p className="font-body text-xs text-aura-muted uppercase tracking-wider mb-3">Whoop</p>
        <div className="flex gap-8">
          <StatPill label="Recovery" value={WHOOP.recovery} unit="%" />
          <StatPill label="HRV" value={WHOOP.hrv} />
          <StatPill label="Sleep" value={WHOOP.sleep} unit="%" />
        </div>
      </div>

      {/* Today's tasks */}
      <div>
        <p className="font-body text-xs text-aura-muted uppercase tracking-wider mb-3">Today</p>
        <ul className="flex flex-col gap-2.5">
          {TASKS.map((task) => (
            <li key={task.label} className="flex items-baseline gap-2">
              <span className="font-body text-sm text-aura-brown">{task.label}</span>
              <span className="font-body text-xs text-aura-muted">— {task.agent}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Active streaks */}
      <div>
        <p className="font-body text-xs text-aura-muted uppercase tracking-wider mb-3">Streaks</p>
        <div className="flex flex-wrap gap-2">
          {STREAKS.map((streak) => (
            <StreakChip key={streak.label} label={streak.label} days={streak.days} />
          ))}
        </div>
      </div>

      {/* Quick access */}
      <div>
        <p className="font-body text-xs text-aura-muted uppercase tracking-wider mb-3">Quick Access</p>
        <div className="flex flex-wrap gap-2">
          {QUICK_ACCESS.map(({ label, to }) => (
            <Link
              key={label}
              to={to}
              className="font-body text-sm text-aura-brown bg-aura-surface hover:bg-aura-blush/20 px-4 py-2 rounded-full transition-colors"
            >
              {label}
            </Link>
          ))}
        </div>
      </div>

      {/* This week at a glance */}
      <div className="border-l-[3px] border-aura-surface pl-4 py-3">
        <p className="font-body text-xs text-aura-muted uppercase tracking-wider mb-3">This Week</p>
        <div className="flex gap-8">
          <div>
            <p className="font-display text-xl text-aura-brown font-semibold">3/5</p>
            <p className="font-body text-xs text-aura-muted">Check-ins</p>
          </div>
          <div>
            <p className="font-display text-xl text-aura-brown font-semibold">4</p>
            <p className="font-body text-xs text-aura-muted">Workouts</p>
          </div>
          <div>
            <p className="font-display text-xl text-aura-brown font-semibold">7.4</p>
            <p className="font-body text-xs text-aura-muted">Avg mood</p>
          </div>
        </div>
      </div>

    </div>
  )
}
```

- [ ] **Step 12: Run all Dashboard tests**

```bash
npx vitest run src/pages/Dashboard.test.tsx
```

Expected: all 7 tests pass

- [ ] **Step 13: Run full test suite**

```bash
npx vitest run
```

Expected: all tests pass, zero failures

- [ ] **Step 14: Verify dashboard in browser**

```bash
npm run dev
```

Open `http://localhost:5173`. Verify:
- Warm cream background
- AURA wordmark in gold
- All 7 dashboard sections render
- Left-border accents visible: blush on check-in, gold on Whoop
- Cormorant Garamond on the greeting and stat values
- DM Sans on body text and labels
- Responsive: on narrow viewport the hamburger appears; tapping it opens the dark drawer

- [ ] **Step 15: Commit**

```bash
cd ..
git add frontend/src/components/ frontend/src/pages/Dashboard.tsx frontend/src/pages/Dashboard.test.tsx
git commit -m "feat: add dashboard page with static placeholder content"
```

---

## Final Steps

- [ ] **Create `.gitignore` at project root**

```
# Python
__pycache__/
*.pyc
backend/aura.db
backend/.env
backend/.venv/

# Node
node_modules/
frontend/dist/

# Env files
.env
frontend/.env

# Superpowers
.superpowers/
```

- [ ] **Run final verification**

Start both services and confirm they communicate:

```bash
# Terminal 1
cd backend && uvicorn main:app --reload

# Terminal 2
cd frontend && npm run dev
```

Open `http://localhost:5173`. The app should render the full dashboard. Then confirm the backend is reachable:

```bash
curl http://localhost:8000/health
# → {"status":"ok","app":"aura"}
```

- [ ] **Final commit**

```bash
git add .gitignore
git commit -m "chore: add project root .gitignore"
```
