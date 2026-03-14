# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Aura** is a personalised health, wellness, and appearance web app for a single user (Shay, Perth AU). The core concept is **The Council** — a team of AI agents with distinct personalities and domains who are proactive, opinionated, and collaborative. This is not a passive tracker; it is an active advisory system.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Tailwind CSS |
| Backend | Python + FastAPI |
| Database | SQLite (Phase 1) → Supabase (Phase 2) |
| AI Agents | Anthropic Claude API (`claude-sonnet`) |
| Integrations | Whoop API, Cronometer API |
| Hosting | Local (Phase 1) → Vercel + Railway (Phase 2) |

---

## Common Commands

### Frontend (`frontend/`)
```bash
npm install          # Install dependencies
npm run dev          # Start dev server (Vite, http://localhost:5173)
npm run build        # Production build
```

### Backend (`backend/`)
```bash
pip install -r requirements.txt   # Install dependencies
uvicorn main:app --reload          # Start dev server
```

---

## Architecture

```
aura/
├── frontend/src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Dashboard, Chat, Agent pages, Onboarding
│   ├── hooks/          # Custom React hooks
│   └── styles/         # Tailwind config + brand tokens
├── backend/
│   ├── agents/         # Agent system prompts, logic, response generation
│   ├── integrations/   # Whoop API, Cronometer API connectors
│   ├── models/         # SQLAlchemy/Pydantic data models
│   ├── routes/         # FastAPI REST endpoints
│   ├── scheduler/      # Background jobs for proactive agent triggers
│   └── main.py         # FastAPI app entry point
```

### Key Data Flow
1. User submits check-in or chat message → FastAPI routes
2. Backend loads user profile + history from SQLite
3. Relevant agent(s) called via Claude API with system prompt + context
4. Response stored as `CouncilMessage`, returned to frontend
5. Scheduler runs background jobs: post-check-in agent responses, Whoop data sync

---

## The Council — Agent Roster

### Phase 1 (Active)
| Agent | Domain | Key Note |
|---|---|---|
| **Rex** | Personal Trainer — strength, body composition, recovery-aware training | Integrates Whoop recovery scores to adjust training intensity |
| **Sage** | Wellbeing & Mental Health — stress, anxiety, burnout, NSDR | Detects emotional patterns across check-in history |
| **Celeste** | Skin Coach — tretinoin/azelaic routine, ingredients, lifestyle-skin links | Do NOT assume rosacea is confirmed — observe over time, suggest derm if warranted |
| **Aurore** | Council Conductor — onboarding, weekly synthesis, cross-domain insights | Leads onboarding flow; generates weekly Council Review |

### Phase 2+ (Planned)
Nadia (nutrition/Cronometer), Ines (hair), Margot (style), Lila (makeup), Dr. Vera (health/longevity)

---

## Core Data Models

```
User           — id, name, email, height, dob, cycle_length
BodyLog        — date, weight, notes
Measurement    — date, waist, hips, glutes, left/right arm, left/right thigh
CheckIn AM     — date, energy, mood, anxiety, sleep_notes, intention
CheckIn PM     — date, day_rating, skincare_done, council_flag, proud_of
Photo          — date, type (body/skin/hair), file_path, notes
Workout        — date, type, exercises (JSON), notes, whoop_recovery_at_time
SkinRoutine    — date, am_completed, pm_completed, active_used (tret/azelaic/none), notes
HabitStreak    — habit_name, current_streak, longest_streak, last_completed
CouncilMessage — timestamp, agent_name, message, triggered_by (checkin/user_message/proactive)
WhoopSnapshot  — date, recovery_score, hrv, sleep_performance, strain
NutritionLog   — date, calories, protein, carbs, fat, notes
```

---

## Brand & Design System

**Colour palette:**
```
Background:     #FAF7F2  (warm cream)
Surface:        #EDE8E0  (soft taupe)
Accent:         #D4A89A  (dusty blush)
Text primary:   #2C2420  (deep warm brown)
Text secondary: #8C7B74  (muted taupe)
Gold highlight: #C9A96E
White:          #FFFDF9
```

**Typography:** Playfair Display or Cormorant Garamond (display) + DM Sans or Jost (body)

**UI principles:** Generous whitespace, soft shadows, rounded cards, subtle grain texture overlay, smooth fades — nothing harsh or generic.

---

## Agent Behaviour Rules

1. **Proactive by default** — agents review check-in data and generate unsolicited responses, flags, and suggestions
2. **Cross-domain awareness** — agents reference each other's domains (Rex knows nutrition data, Celeste knows stress levels)
3. **Honest, not flattering** — flag when things aren't working; don't default to validation
4. **Medical boundaries** — Dr. Vera and Celeste flag clinical concerns but always defer to professional consultation; they do not diagnose
5. **Style frameworks as tools** — Margot explores Kibbe/colour analysis analytically with Shay rather than accepting labels as fact
6. **Agent voice** — each agent has a distinct voice; never say "Great question!" or use filler affirmations

---

## Build Phases

**Phase 1 (current):** Project setup, brand shell, Aurore-led onboarding, Dashboard, morning/evening check-ins, Council chat (Rex + Sage + Celeste), basic data storage, Whoop API integration.

**Phase 2:** Progress photos, weight/measurement charts, habit streaks, proactive post-check-in triggers, Cronometer integration, individual agent pages.

**Phase 3:** Remaining agents, weekly Council Review, notifications, cross-agent chat tagging, Supabase migration, Vercel + Railway deployment.
