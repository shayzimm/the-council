# Aura — Sub-project 1: Scaffold & Brand Shell

**Date:** 2026-03-14
**Status:** Approved
**Scope:** Phase 1 foundation — project structure, design system, layout shell, and dashboard skeleton. No live data. Establishes the visual and architectural foundation every subsequent sub-project builds on.

---

## Project Decomposition

Phase 1 of the Aura brief is decomposed into six sequential sub-projects, each with its own spec → plan → implementation cycle:

1. **Scaffold & Brand Shell** ← this spec
2. Onboarding flow (Aurore-led conversational profile builder)
3. Dashboard (live data, check-in state, Whoop snapshot read)
4. Daily check-ins (morning + evening flows + post-check-in agent responses)
5. Council Chat (chat UI + Claude API integration for Rex, Sage, Celeste)
6. Whoop API integration (full connector + data sync — feeds into sub-project 3's live data)

> **Note on sub-project 3/6 sequencing:** Sub-project 3 requires basic Whoop data. The two options when we get there: (a) sub-project 6 is built first and 3 consumes it, or (b) sub-project 3 implements a minimal read-only Whoop snapshot and 6 expands it. This will be resolved in the sub-project 3 spec.

---

## Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Frontend | Vite + React 18 + TypeScript | Fast dev server, modern standard, TS catches bugs early |
| Styling | Tailwind CSS | Utility-first, brand tokens baked into config |
| Routing | React Router v6 | Standard SPA routing |
| Backend | Python + FastAPI | Per brief |
| ORM | SQLAlchemy + Pydantic v2 | Per brief |
| Database | SQLite (Phase 1) | Local, zero-config |
| Fonts | Google Fonts CDN | Cormorant Garamond + DM Sans, loaded via `<link>` in `index.html` (not CSS `@import`) to avoid render-blocking FOUT |

---

## Project Structure

```
aura/
├── frontend/
│   ├── src/
│   │   ├── components/         # Shared UI primitives (Button, Card, StatPill, StreakChip)
│   │   ├── layout/             # AppShell, TopNav, MobileDrawer, PageWrapper
│   │   ├── pages/              # Dashboard, and stubs for Council, Progress, Settings, CheckIn
│   │   ├── hooks/              # Custom React hooks (empty placeholder in this sub-project)
│   │   ├── types/              # Shared TypeScript interfaces (index.ts stub)
│   │   ├── styles/             # globals.css (Tailwind directives + base overrides)
│   │   ├── App.tsx             # Router setup, AppShell composition, route definitions
│   │   └── main.tsx            # Entry point — mounts <App /> only
│   ├── index.html              # Google Fonts <link> tags live here
│   ├── .env.example            # Documents expected env vars (VITE_API_URL)
│   ├── vite-env.d.ts           # Vite env type declarations
│   ├── tailwind.config.ts      # Brand tokens
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── backend/
│   ├── main.py                 # FastAPI app, CORS, router registration
│   ├── database.py             # SQLAlchemy engine + session factory
│   ├── models/                 # SQLAlchemy table definitions (empty placeholder)
│   ├── routes/
│   │   └── health.py           # GET /health — confirms API is running
│   └── requirements.txt
│
├── docs/
│   └── superpowers/specs/      # Design specs
├── .gitignore                  # Includes .env, .superpowers/, __pycache__, node_modules
├── AURA_PROJECT_BRIEF.md
└── CLAUDE.md
```

---

## Design System

All brand tokens defined in `tailwind.config.ts` and referenced by name throughout the codebase. Raw hex values never appear in component files.

### Colour Tokens

| Token | Hex | Usage |
|---|---|---|
| `aura-cream` | `#FAF7F2` | Page background |
| `aura-surface` | `#EDE8E0` | Cards, inputs, surface elements |
| `aura-blush` | `#D4A89A` | Check-in accent, wellbeing domain |
| `aura-brown` | `#2C2420` | Primary text, dark surfaces (nav drawer) |
| `aura-muted` | `#8C7B74` | Secondary text, labels, inactive nav |
| `aura-gold` | `#C9A96E` | Logo, Whoop/data accent, gold highlights |
| `aura-white` | `#FFFDF9` | High-contrast white, top nav background |

### Typography Tokens

| Token | Font | Usage |
|---|---|---|
| `font-display` | Cormorant Garamond | Headings, greeting, agent names, wordmark |
| `font-body` | DM Sans | All body text, labels, nav links, buttons |

### Visual Conventions

- **Left-border accents** (3px solid) are the primary section differentiator — blush for check-in/wellbeing, gold for data/Whoop
- **Shadows:** `shadow-sm` only — nothing harsh
- **Border radius:** `rounded-lg` for cards, `rounded-full` for avatars and pills
- **Spacing:** generous — sections breathe, no cramming
- **Dividers:** whitespace only — no horizontal rules between content blocks

---

## Layout Shell

### Routing

`App.tsx` owns all route definitions. `main.tsx` only bootstraps React and mounts `<App />`.

| Path | Page | Notes |
|---|---|---|
| `/` | Redirect → `/dashboard` | |
| `/dashboard` | Dashboard | |
| `/council` | Council stub | Placeholder page |
| `/progress` | Progress stub | Placeholder page |
| `/settings` | Settings stub | Placeholder page |
| `/checkin` | Check-in stub | Placeholder page — linked from dashboard |

### Desktop (≥768px)

- Fixed top nav bar, `aura-white` background, 1px bottom border in `aura-surface`
- Left: "AURA" wordmark — Cormorant Garamond, `aura-gold`, wide letter-spacing
- Right: nav links in DM Sans — active link has a 1px blush underline, inactive in `aura-muted`
- Content area: max-width `1024px`, centred, padded horizontally

### Mobile (<768px)

- Slim top bar: wordmark left, hamburger icon right, both in `aura-brown`
- Hamburger opens a full-height left drawer — `aura-brown` background, nav links in `aura-cream`, stacked vertically
- Drawer closes on nav link tap or tap outside
- Content fills full width with consistent horizontal padding

### PageWrapper Component

Wraps every page with consistent vertical padding and max-width constraint. Pages render content only — no layout concerns.

---

## Dashboard Page

Renders real structure with static placeholder data. No API calls in this sub-project.

**Content blocks, top to bottom:**

1. **Greeting header**
   - "Good morning, Shay" in Cormorant Garamond, large
   - Today's date in `aura-muted`
   - Static placeholder intention/insight line in italic `aura-muted`

2. **Check-in prompt**
   - Full-width block, 3px blush left-border accent
   - "Morning check-in · ~2 mins" with arrow
   - Tappable — routes to `/checkin` stub
   - Conditionally hidden if check-in already completed today (static: always shown in this sub-project)

3. **Whoop snapshot**
   - Full-width block, 3px gold left-border accent
   - Three inline stat pills: Recovery %, HRV (ms), Sleep score
   - Static placeholder values

4. **Today's tasks**
   - Section label: "TODAY" in small caps, `aura-muted`
   - 3 static placeholder task rows (e.g. "Upper body — Rex", "Tret night — Celeste", "10 min NSDR — Sage")
   - Agent name in `aura-muted`, task in `aura-brown`

5. **Active streaks**
   - Row of streak chips: habit name + day count
   - Static placeholder data

6. **Quick access**
   - Row of agent shortcut buttons: Rex, Celeste, Sage, The Council
   - All link to `/council` stub (no per-agent routing yet)
   - Static in this sub-project

7. **This week at a glance**
   - Mini summary block with placeholder values: check-in scores, workouts completed
   - Rendered as a static placeholder — no data computation in this sub-project

**Spacing:** Each block separated by generous vertical margin. No dividers — whitespace does the work.

---

## Backend

### Endpoint

```
GET /health
→ { "status": "ok", "app": "aura" }
```

### CORS

Configured to allow requests from `http://localhost:5173` (Vite dev server). **Dev-only** — to be made environment-variable-driven before any deployment.

### Database

SQLAlchemy engine and session factory wired and ready in `database.py`. No tables defined yet.

---

## Environment Variables

| Variable | Location | Purpose |
|---|---|---|
| `VITE_API_URL` | `frontend/.env` | Backend base URL (default: `http://localhost:8000`) |

`frontend/.env.example` documents this. Actual `.env` is gitignored.

---

## Out of Scope for This Sub-project

- Live API data (Whoop, Claude)
- Check-in forms (the `/checkin` route is a stub only)
- Council chat
- Authentication
- Any database reads/writes
- Agent logic
