# Aura — Project Instructions & Architecture Guide

**Last updated:** 2026-03-15
**Purpose:** Central reference for all Aura development — used by Claude Code (implementation) and Claude.ai (brainstorming/design). Keep this document updated as the project evolves.

---

## How This Project Is Built

Aura is developed collaboratively across two contexts:

- **Claude.ai (this project):** Brainstorming, architecture design, spec writing, design reviews. This is where new ideas are explored, architecture sketches are created, and implementation plans are refined before handing them to Claude Code.
- **Claude Code:** Implementation. Takes specs and architecture docs from this project and builds working code in the GitHub repository.

When designing new features or systems, the workflow is:
1. Brainstorm and design here (Claude.ai)
2. Produce a spec or architecture doc
3. Add it to project files for persistence
4. Claude Code picks it up and implements within the existing codebase

**Important:** Claude Code should NOT be paused while brainstorming happens here. The architecture docs target future sub-projects. Claude Code continues working on the current sub-project, and picks up new architecture when it reaches the relevant sub-project.

---

## Current State (as of 2026-03-15)

### What's built
- **Sub-project 1 (Scaffold & Brand Shell):** Complete. Vite + React + TypeScript frontend with Tailwind brand tokens, responsive AppShell (top nav desktop / hamburger drawer mobile), static dashboard with all 7 content blocks, FastAPI backend with health endpoint, SQLAlchemy wired but no tables yet.
- **Sub-project 3 (Dashboard live data):** Near end of implementation. Check current repo for exact status.

### What's fully designed (architecture docs complete)
Seven architecture documents exist in the project files, covering the entire Phase 1 system end-to-end:

| Doc | Scope | Implements in |
|---|---|---|
| **`council-round-architecture.md`** | How agents collaborate: sequential responses, shared context, Aurore triage, cross-agent referencing. Models: `CouncilRound`, updated `CouncilMessage`. Agent registry with system prompts. | Sub-projects 4–5 |
| **`checkin-architecture.md`** | Low-friction check-ins: conversational + quick-tap modes, three-step API flow (prepopulate → extract → confirm), Whoop pre-population, Council Round trigger. Frontend state machine. | Sub-project 4 |
| **`pattern-detection-architecture.md`** | Proactive observations: rule-based detectors + Aurore interpretation, `AgentInsight` model, severity gating, three trigger contexts (post-check-in, nightly, weekly). | Sub-projects 4–5 (post-check-in), Phase 2 (scheduled) |
| **`onboarding-architecture.md`** | Progressive onboarding: 3 layers (essential → domain deep-dives → integrations), conversational extraction, Council introduction round. **Full Goal system** with north star/milestone/focus hierarchy. | Sub-project 2 |
| **`council-chat-architecture.md`** | Chat UI: component hierarchy, grouped round rendering, @mention system, agent presence bar, suggestion chips, streaming strategy (polling → SSE → WebSocket progression), TypeScript interfaces. | Sub-project 5 |
| **`whoop-integration-architecture.md`** | Whoop v2 API: OAuth 2.0 flow, token management, data sync strategy (daily scheduled + on-demand), `WhoopSnapshot`/`WhoopSleep`/`WhoopWorkout` models, 30-day backfill, error handling. | Sub-project 6 |
| **`weekly-review-architecture.md`** | Aurore's editorial weekly synthesis: structured review format (opening → narrative → working/attention → agent one-liners → focus points → goal progress), generation flow, focus-point feedback loop. | Late Phase 1 or Phase 2 |

### What's not yet designed
- **Sub-project 2/3 implementation plans** — step-by-step build plans for Claude Code (like the sub-project 1 plan that exists). To be created when Claude Code is ready for each.

---

## Sub-project Sequence (Phase 1)

1. ~~**Scaffold & Brand Shell**~~ ✅ Complete
2. **Onboarding** — Aurore-led conversational profile builder + Goal system. **Use `onboarding-architecture.md`.**
3. **Dashboard** (live data) — In progress. Check-in state, Whoop snapshot read.
4. **Daily Check-ins** — Morning + evening flows + post-check-in Council Round responses + post-check-in pattern detection. **Use `checkin-architecture.md`, `council-round-architecture.md`, and `pattern-detection-architecture.md`.**
5. **Council Chat** — Chat UI + Claude API integration + proactive message rendering. **Use `council-chat-architecture.md` and `council-round-architecture.md`.**
6. **Whoop API integration** — Full connector + data sync. **Use `whoop-integration-architecture.md`.**

### Sequencing notes
- Sub-project 3 needs basic Whoop data. Either sub-project 6 goes first, or 3 implements a minimal read-only snapshot and 6 expands it.
- The **Council Round system is shared infrastructure** for check-ins (sub-project 4), chat (sub-project 5), and the weekly review. Build the round orchestration service first during sub-project 4, then sub-project 5 and the weekly review consume it.
- The **Goal system** (in `onboarding-architecture.md`) should be implemented during sub-project 2 but is referenced by check-in rounds, pattern detection, and the weekly review. Goals are a first-class concept throughout the system.
- Sub-projects 4 and 5 are the most architecture-heavy. The docs were designed so the round orchestration service is built once and consumed by both.

### Handoff points (when to give Claude Code new architecture)
- **Before sub-project 2:** Add `onboarding-architecture.md` to the repo. Update CLAUDE.md with Goal and UserProfile models.
- **Before sub-project 4:** Add `council-round-architecture.md`, `checkin-architecture.md`, `pattern-detection-architecture.md` to the repo. Update CLAUDE.md with CouncilRound, AgentInsight, updated CouncilMessage, updated CheckIn models. Add agent registry.
- **Before sub-project 5:** Add `council-chat-architecture.md` to the repo. The round orchestration backend should already exist from sub-project 4.
- **Before sub-project 6:** Add `whoop-integration-architecture.md` to the repo. Add WhoopToken, WhoopSnapshot, WhoopSleep, WhoopWorkout models to CLAUDE.md.

---

## Key Architecture Decisions

These decisions were made during brainstorming and should be respected during implementation:

### 1. Council Rounds are the unit of agent collaboration
Every trigger (check-in, chat, Whoop sync, proactive detection, weekly review) creates a `CouncilRound`. Agents respond sequentially within a round, each seeing what came before. This is not optional — independent parallel agent calls produce disjointed advice.

### 2. Aurore always triages first
Aurore is the routing brain. She determines which agents respond and in what order based on the data. She outputs a `<triage>` block with JSON (agent_order, flags, summary, suggestions) that the service parses. This keeps routing logic in the AI layer, not hardcoded.

### 3. Check-ins use conversational extraction by default
Natural language input → lightweight Claude API extraction → user confirms parsed values → save + trigger round. Quick-tap is the fallback, not the default. Both modes converge on the same confirm endpoint.

### 4. Pattern detection is two-layered
Rule-based detectors generate candidates. Aurore filters and interprets them. This prevents alert fatigue while ensuring real patterns are surfaced.

### 5. AgentInsights are distinct from CouncilMessages
Insights are persistent state (dashboard cards). Messages are conversational (chat timeline). An insight can trigger a round, and agents can reference active insights in their responses, but they're separate models with different lifecycles.

### 6. Agents can and should disagree
The system explicitly supports conflicting recommendations. The UI surfaces "Council is split" moments and lets Shay choose. This is a feature, not a bug.

### 7. Goals are a first-class concept
Every agent's advice anchors to explicit goals. Goals have a three-tier hierarchy: North Star (qualitative, long-term) → Milestone (measurable, time-bound) → Focus (current priority, max 2–3). Goals are collected during onboarding, refined during the first week, tracked automatically, and reviewed monthly.

### 8. Onboarding is progressive
Three layers: essential setup (~5 min, required), domain deep-dives (first week, agent-led), integration connections (whenever ready). The app is usable after Layer 1. The profile deepens through natural use, not homework.

### 9. The Weekly Review feeds back into the system
Aurore's weekly focus points aren't just text — they influence daily triage, generate short-term Goals, and inform daily task recommendations for the following week. Each review references the previous one's focus points to assess follow-through.

### 10. Polling first, streaming later
Council Chat uses polling in Phase 1 (simple, zero infrastructure). Phase 2 upgrades to SSE. WebSocket only if bidirectional real-time features are needed.

---

## Data Models — Complete List

### Original Models (from CLAUDE.md)
`User`, `BodyLog`, `Measurement`, `Photo`, `Workout`, `SkinRoutine`, `HabitStreak`, `WhoopSnapshot` (basic), `NutritionLog`

### New Models (from architecture docs)
- **`CouncilRound`** — Groups agent messages from a single trigger event. Fields: triggered_by, trigger_reference_id, triage_summary, agent_order, status.
- **`AgentInsight`** — Persistent pattern observations. Fields: pattern_type, severity, owning_agent, title, detail, supporting_data, status, pattern_key (dedup).
- **`Goal`** — Three-tier goal system. Fields: goal_type (north_star/milestone), parent_id, domain, linked_agent, title, target_value, target_unit, current_value, deadline, status, priority (focus/active/background).
- **`UserProfile`** — Extended profile from onboarding. Fields: height, weight, DOB, location, training details, skin type/concerns, wellbeing baselines, cycle info, supplements, onboarding_layer.
- **`WhoopToken`** — OAuth token storage. Fields: access_token, refresh_token, expires_at, scope, status.
- **`WhoopSleep`** — Detailed sleep data. Fields: stage breakdown, sleep need, efficiency, consistency.
- **`WhoopWorkout`** — Detailed workout data. Fields: sport, strain, heart rate, zones, distance.
- **`WeeklyReview`** — Structured weekly review. Fields: opening_line, narrative, whats_working, needs_attention, focus_points, goal_snapshot.

### Updated Models
- **`CouncilMessage`** — Now includes: round_id, sequence_order, internal_reasoning, mentions, in_reply_to, visibility.
- **`CheckInAM`** — Now includes: raw_input, mode (conversational/quick_tap/backfill), whoop_recovery/hrv/sleep_score snapshots.
- **`CheckInPM`** — Now includes: raw_input, mode, tasks_completed (JSON), whoop_strain.
- **`WhoopSnapshot`** — Expanded with full recovery, sleep summary, and cycle data. One record per day.

---

## Implementation Guidelines for Claude Code

When picking up work from these architecture docs:

1. **Read the relevant architecture doc(s) before starting a sub-project.** They contain data models, API contracts, component structures, and example flows.
2. **Models inherit from the existing `Base` in `database.py`.** The sketches use placeholder classes — replace with proper SQLAlchemy model definitions.
3. **The Anthropic SDK calls are commented out in sketches.** Uncomment and wire up with the `anthropic` Python package. Use `claude-sonnet-4-20250514` as the model.
4. **Async routes are expected.** FastAPI supports `async def` natively. The round orchestration service uses async throughout.
5. **Agent system prompts live in the agent registry** (backend module, not in route handlers). Keep them centralised and version-controlled.
6. **Don't skip the internal_reasoning field.** Storing agent chain-of-thought is critical for debugging weird recommendations. It's not shown to the user but it's invaluable during development.
7. **Test the round orchestration with a simple check-in trigger first.** Get Aurore triage + one agent responding before wiring up all three domain agents.
8. **New Tailwind tokens may be needed.** Agent accent colours (e.g. `aura-rust` for Rex, `aura-sage` for Sage) should be added to `tailwind.config.ts` when the Council Chat is built.

---

## Brand & Design Reminders

- **Raw hex values never appear in component files.** Always use Tailwind token names (`aura-cream`, `aura-blush`, etc.)
- **Left-border accents (3px solid)** are the primary section differentiator — blush for check-in/wellbeing, gold for data/Whoop
- **Font pairing:** Cormorant Garamond (display/headings) + DM Sans (body/labels)
- **Shadows:** `shadow-sm` only. Nothing harsh.
- **Spacing:** generous. Sections breathe. No cramming. No horizontal rules — whitespace does the work.
- **Agent voice:** each agent has a distinct personality. Never use filler affirmations. Never say "Great question!"
- **Agent accent colours:** Aurore = `aura-gold`, Celeste = `aura-blush`, Rex = warm terracotta/rust, Sage = soft sage green. Used subtly for avatars, names, mention highlights.

---

## Open Questions / Future Brainstorming Topics

- **Sub-project implementation plans** — Step-by-step build plans for Claude Code (chunked tasks, test-first, clear file paths). To be created as needed before each sub-project.
- **Phase 2 agent additions** — Nadia (nutrition/Cronometer) will need new detectors, cross-domain connections, and onboarding deep-dive.
- **Cronometer API integration** — Similar pattern to Whoop but for nutrition data. Nadia's primary data source.
- **Progress photos** — Upload, storage, comparison gallery, agent-driven analysis.
- **Notification system** — Push notifications for check-in prompts, streak nudges, proactive insights. Smart timing based on Whoop wake/sleep data.
- **Individual agent pages** — Domain-specific dashboards (Rex: workout history, Celeste: skin timeline, Sage: mood trends).
- **Supabase migration** — Phase 2 database upgrade. Schema migration strategy from SQLite.
