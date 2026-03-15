# Onboarding Architecture

**Date:** 2026-03-15
**Status:** Design sketch — to be implemented as sub-project 2
**Depends on:** Scaffold & Brand Shell (sub-project 1), Council Round Architecture (for agent introduction round)

---

## Overview

Onboarding is Shay's first experience with the Council. It must feel like a conversation with someone genuinely interested in understanding her — not a registration form. Aurore leads the flow, collects structured data through natural language, and introduces each Council member in character.

Onboarding is **progressive** — split across three layers so Shay can start using the app in five minutes, with the profile deepening over the first week of natural use.

**Goals are a first-class concept.** Every agent's advice anchors to explicit goals Shay sets during onboarding. Goals are not an afterthought — they're woven into each topic as it's discussed.

---

## Progressive Onboarding Layers

### Layer 1 — Essential Setup (required, ~5 minutes)
Collected before first use. Enough for Rex, Sage, and Celeste to function.

**Topics covered:**
- Name, basic stats (height, weight, DOB)
- Training overview (frequency, type, goals)
- Skin routine (brief) + key concerns
- Wellness baseline (stress, anxiety, sleep — rough self-assessment)
- Top-level goals across all domains
- Council introduction (Aurore introduces Rex, Sage, Celeste in character)

**Ends with:** Dashboard shown for the first time, populated with first-day tasks and the Council's initial observations.

### Layer 2 — Domain Deep-Dives (first week, prompted naturally)
Each agent leads their own onboarding conversation when their domain becomes relevant:

- **Rex** asks about specific training goals, current lifts, body composition targets, and programming preferences the first time a workout is logged or training comes up.
- **Celeste** asks detailed product questions, active ingredient history, sensitivities, and skin photo baseline the first time skincare appears in a check-in or she gives her first recommendation.
- **Sage** explores anxiety history, coping practices, and wellbeing goals when the first elevated anxiety check-in happens or stress is mentioned.
- **Aurore** fills in any remaining profile gaps (cycle info, medications, supplements) via a gentle follow-up prompt during the first week.

These appear as a chat-style interaction on the relevant agent's first meaningful contact — not as a separate "onboarding step 2" page.

### Layer 3 — Integration Connections (whenever ready)
Prompted from dashboard cards, not forced during onboarding:
- "Connect Whoop to unlock recovery-aware training" → OAuth flow
- "Link Cronometer for nutrition tracking" (Phase 2)
- "Take your first progress photo" → guided photo capture

---

## Aurore's Conversational Flow (Layer 1)

Rather than stepping through fields one by one, Aurore uses **four open prompts** that each cover a natural topic cluster. The system extracts structured data from the responses and confirms.

### Flow Structure

```
WELCOME
  → Aurore introduces herself
  → Sets expectations ("This takes about 5 minutes")

TOPIC 1: "Tell me about your week"
  → Extracts: training_frequency, training_type, work_status, study_status, location
  → Follow-up: "What are you working toward with your training?"
  → Extracts: training_goals (north star + milestones)

TOPIC 2: "Tell me about your skin and routine"
  → Extracts: skin_type, skin_concerns, current_routine_brief, active_medications
  → Follow-up: "What would you love to see change?"
  → Extracts: skin_goals

TOPIC 3: "How's your headspace generally?"
  → Extracts: stress_baseline, anxiety_baseline, sleep_baseline, energy_baseline
  → Follow-up: "What does feeling good look like for you?"
  → Extracts: wellbeing_goals

TOPIC 4: "Anything else I should know?"
  → Catches: supplements, cycle info, injuries, preferences, context
  → Optional — user can skip

CONFIRMATION
  → Show parsed profile as editable summary
  → User confirms or adjusts

COUNCIL INTRODUCTION
  → Aurore introduces Rex, Sage, Celeste in character
  → Each agent gives a brief, personalised first message based on the profile
  → This is a special "introduction" Council Round

DASHBOARD
  → First view of the dashboard with initial tasks
```

### Topic Prompts (Aurore's voice)

**Welcome:**
> "Hi Shay. I'm Aurore — I coordinate The Council, your personal advisory team. Before I introduce everyone, I'd love to understand you a little. This takes about five minutes, and you can always update things later."

**Topic 1:**
> "Tell me about your week — training, work, study, whatever paints the picture."

**Topic 1 follow-up (goals):**
> "What are you working toward with your body and training right now? Big picture is fine — we'll get specific over time."

**Topic 2:**
> "Now skin. What's your current routine, and what are you dealing with? Don't worry about being precise — Celeste will dig into the details once she's had a chance to get to know your skin."

**Topic 2 follow-up (goals):**
> "If you could change one thing about your skin, what would it be?"

**Topic 3:**
> "How's your headspace been lately? Stress, anxiety, sleep — give me the honest version, not the polished one."

**Topic 3 follow-up (goals):**
> "What does feeling good look like for you? Not perfect — just genuinely good."

**Topic 4:**
> "Anything else I should know? Medications, supplements, injuries, things that affect your day-to-day — or skip this if you've covered it."

---

## Goal System Architecture

### Goal Hierarchy

```
North Star Goal (qualitative, long-term)
  └── Milestone Goal (measurable, time-bound)
       └── linked to Agent(s) who track it
       └── linked to Focus Area (current priority)
```

### Examples

```
North Star: "Build an hourglass physique"
  ├── Milestone: "Reach 58kg by June 2026" (Rex)
  ├── Milestone: "Complete 4 training sessions/week for 8 weeks" (Rex)
  └── Milestone: "Increase glute measurement by 2cm in 12 weeks" (Rex)

North Star: "Get my anxiety under control"
  ├── Milestone: "Average anxiety below 5 for a full month" (Sage)
  ├── Milestone: "Complete NSDR 5x/week for 4 weeks" (Sage)
  └── Milestone: "No anxiety spikes above 8 for 2 consecutive weeks" (Sage)

North Star: "Clear, resilient skin"
  ├── Milestone: "Build tret tolerance to every other night by April" (Celeste)
  ├── Milestone: "Complete PM skincare routine 6/7 nights for 4 weeks" (Celeste)
  └── Milestone: "Take weekly skin photo for 8 consecutive weeks" (Celeste)
```

### Goal Data Model

```
Goal
  id              Integer PK
  goal_type       Enum: north_star | milestone
  parent_id       Integer FK → Goal.id, nullable (milestones link to north stars)
  domain          String — "training", "skin", "wellbeing", "nutrition", "general"
  linked_agent    String — primary agent who owns this goal ("rex", "sage", etc.)
  title           String(200) — human-readable, e.g. "Build tret tolerance to every other night"
  description     Text, nullable — additional context
  target_value    Float, nullable — for measurable milestones (e.g. 58.0 for weight)
  target_unit     String, nullable — "kg", "days", "score", "%", etc.
  current_value   Float, nullable — last measured value (updated by check-ins, Whoop, etc.)
  deadline        Date, nullable — target date for milestones
  status          Enum: active | achieved | paused | abandoned
  priority        Enum: focus | active | background
                  focus = currently prioritised (agents emphasise this)
                  active = being tracked but not top priority
                  background = set but not actively pushed
  created_at      DateTime
  achieved_at     DateTime, nullable
  notes           Text, nullable — agent observations, user notes
```

### Goal Lifecycle

1. **Created during onboarding** — Aurore extracts goals from conversational input and proposes structured milestones
2. **Refined in first week** — domain agents propose additional milestones during Layer 2 deep-dives
3. **Tracked automatically** — check-in data, Whoop data, streak data update `current_value` where applicable
4. **Referenced in rounds** — agents anchor advice to active goals. "This moves you toward your anxiety target." "You're 2kg from your weight milestone."
5. **Celebrated on achievement** — when `current_value` meets `target_value`, the owning agent acknowledges it in the next round
6. **Reviewed monthly** — Aurore prompts a goal review: what's still relevant, what's shifted, new milestones
7. **Evolved over time** — goals can be paused, abandoned (no judgment), or replaced

### Focus Areas

The `priority: focus` flag determines what the Council emphasises right now. Max 2-3 focus goals at a time. Aurore's triage weighs focus goals more heavily when deciding agent order and response depth.

During onboarding, Aurore asks: "Of everything we've talked about, what matters most to you right now?" The answer sets initial focus priorities.

Users can change focus areas from a Goals section in Settings, or Aurore can suggest shifts during monthly reviews.

---

## Council Introduction Round

After onboarding data is confirmed, a special **introduction round** fires. This uses the Council Round architecture but with a unique trigger type (`onboarding`) and a modified prompt:

Each agent receives the full onboarding profile and their relevant goals. Their instruction is: "This is your first time meeting Shay. Introduce yourself briefly and in character. Reference something specific from her profile. Keep it under 3 sentences. Set expectations for what you'll be paying attention to."

This produces personalised introductions, not canned text. Rex sees the training goals and responds to them specifically. Sage sees the anxiety baseline and acknowledges it. Celeste sees the tret routine and has an opinion.

The introduction messages are stored as a Council Round (triggered_by: `onboarding`) and appear in the Council Chat history as the first conversation.

---

## Onboarding Extraction

Same pattern as check-in extraction — lightweight Claude API call with a constrained system prompt that outputs JSON.

### Extraction System Prompt (Topic 1: Training & Lifestyle)

```
You extract structured profile data from a natural conversational response.

The user (Shay) is describing her typical week. Extract:
- training_frequency: number of sessions per week (integer)
- training_type: brief description (e.g. "upper/lower split", "PPL", "CrossFit")
- training_experience: "beginner" | "intermediate" | "advanced" (infer from context)
- work_status: "full_time" | "part_time" | "casual" | "not_working" | null
- study_status: "full_time" | "part_time" | null
- location: city/region if mentioned, null otherwise

Set fields to null if not mentioned. Do not infer values that aren't at least implied.

RESPOND ONLY WITH JSON. No preamble, no markdown.
```

### Extraction System Prompt (Goals — used after each topic follow-up)

```
You extract goals from a natural conversational response about what the user wants to achieve.

For each goal mentioned, extract:
- title: concise goal statement
- domain: "training" | "skin" | "wellbeing" | "nutrition" | "general"
- goal_type: "north_star" (qualitative/long-term) or "milestone" (measurable/time-bound)
- target_value: number if mentioned, null otherwise
- target_unit: unit if mentioned ("kg", "days", "%"), null otherwise
- deadline: date if mentioned, null otherwise
- linked_agent: which agent owns this ("rex", "sage", "celeste", "aurore")

Return a JSON array of goals. If no clear goals are mentioned, return an empty array.
Users often state goals vaguely. Extract what you can and note what's vague.

RESPOND ONLY WITH JSON. No preamble, no markdown.
```

---

## Profile Data Model

Extends the existing `User` model:

```
UserProfile
  id                    Integer PK
  user_id               Integer FK → User.id (or just extend User directly)

  # Basic stats
  height_cm             Float
  current_weight_kg     Float, nullable
  dob                   Date
  location              String, nullable

  # Lifestyle
  work_status           String, nullable
  study_status          String, nullable
  training_frequency    Integer, nullable — sessions per week
  training_type         String, nullable
  training_experience   String, nullable — beginner/intermediate/advanced

  # Skin
  skin_type             String, nullable — "dry", "oily", "combination", "normal", "sensitive"
  skin_concerns         JSON, nullable — ["aging", "laxity", "dullness", "possible rosacea"]
  current_routine_brief Text, nullable — free text summary from onboarding
  active_medications    JSON, nullable — ["tretinoin 0.025%", "azelaic acid 15%"]

  # Wellbeing baselines
  stress_baseline       Integer, nullable — 1-10 self-assessment
  anxiety_baseline      Integer, nullable — 1-10
  sleep_baseline        Integer, nullable — 1-10
  energy_baseline       Integer, nullable — 1-10

  # Cycle
  cycle_length          Integer, nullable — days
  cycle_tracking        Boolean, default False

  # Supplements
  supplements           JSON, nullable — ["magnesium", "vitamin D", "omega-3"]

  # Meta
  onboarding_completed_at   DateTime, nullable
  onboarding_layer          Integer, default 0 — 0=not started, 1=essential, 2=deep-dives, 3=full
  profile_last_reviewed     DateTime, nullable — last Aurore-led profile refresh

  created_at            DateTime
  updated_at            DateTime
```

---

## API Endpoints

### Onboarding Flow

```
POST /onboarding/start
  → Creates UserProfile record, returns welcome message from Aurore

POST /onboarding/extract
  Body: { topic: "lifestyle" | "skin" | "wellbeing" | "other" | "goals", raw_input: str }
  → Returns extracted structured data for confirmation

POST /onboarding/confirm-topic
  Body: { topic: str, extracted_data: dict, goals: list[dict] }
  → Saves confirmed data to UserProfile + creates Goal records

POST /onboarding/complete
  → Marks onboarding_completed_at, sets onboarding_layer=1
  → Triggers Council Introduction Round
  → Returns introduction messages from each agent

GET /onboarding/status
  → Returns current onboarding state (which topics completed, which layer)
```

### Goals

```
GET /goals
  → Returns all goals, filterable by status, domain, priority, linked_agent

GET /goals/focus
  → Returns only focus-priority goals (max 2-3)

POST /goals
  Body: { goal_type, domain, linked_agent, title, target_value?, deadline?, priority }
  → Creates a new goal (can be done post-onboarding too)

PUT /goals/{id}
  Body: { any updatable fields }
  → Update goal (status, priority, current_value, notes, deadline)

POST /goals/{id}/achieve
  → Marks goal as achieved, sets achieved_at, triggers celebration in next round

POST /goals/review
  → Aurore-initiated goal review. Returns current goals with suggested updates.
```

### Profile

```
GET /profile
  → Returns full UserProfile

PUT /profile
  Body: { any updatable fields }
  → Update profile fields

POST /profile/refresh
  → Triggers Aurore-led profile refresh conversation (re-onboarding light)
```

---

## Frontend Components

### Onboarding Page (`/onboarding`)

```
OnboardingPage.tsx
  ├── OnboardingWelcome.tsx        — Aurore's intro, "Let's get started" CTA
  ├── ConversationStep.tsx         — Reusable: shows Aurore's prompt, text area, submit
  │   ├── Renders Aurore's question
  │   ├── User types response
  │   ├── Submit → extract → show confirmation
  │   └── Confirm → save → next topic
  ├── GoalExtraction.tsx           — Shows extracted goals as editable cards
  │   ├── Each goal: title, domain tag, optional target/deadline
  │   ├── Add/remove/edit goals
  │   └── Confirm batch
  ├── ProfileSummary.tsx           — Full profile review before finalising
  │   ├── All extracted data shown as editable sections
  │   ├── Goals grouped by domain
  │   └── "Looks good" / "Let me adjust" actions
  ├── CouncilIntroduction.tsx      — Agent introduction messages
  │   ├── Each agent's avatar + name + personalised message
  │   ├── Staggered reveal (Aurore → Rex → Sage → Celeste)
  │   └── "Meet your dashboard" CTA at the end
  └── FocusPicker.tsx              — "What matters most right now?"
      ├── Shows all goals as selectable cards
      ├── User picks 2-3 as focus areas
      └── Sets priority: focus on selected goals
```

### State Machine

```
NOT_STARTED
  → (user hits /onboarding or first app load)
WELCOME
  → (user taps "Let's get started")
TOPIC_LIFESTYLE
  → (extract → confirm)
TOPIC_LIFESTYLE_GOALS
  → (extract goals → confirm)
TOPIC_SKIN
  → (extract → confirm)
TOPIC_SKIN_GOALS
  → (extract goals → confirm)
TOPIC_WELLBEING
  → (extract → confirm)
TOPIC_WELLBEING_GOALS
  → (extract goals → confirm)
TOPIC_OTHER (optional, skippable)
  → (extract → confirm)
FOCUS_PICKER
  → (user selects 2-3 focus goals)
PROFILE_SUMMARY
  → (user reviews and confirms everything)
COUNCIL_INTRODUCTION
  → (introduction round fires, agent messages stream in)
COMPLETE
  → (redirect to /dashboard)
```

---

## Layer 2: Domain Deep-Dives (First Week)

These are NOT separate onboarding pages. They're conversational prompts that appear the first time an agent has a meaningful reason to learn more.

### Trigger Conditions

| Agent | Trigger | What they ask |
|---|---|---|
| Rex | First workout logged OR first check-in where training is mentioned | Current program details, specific lifts, body comp targets, calisthenics interest, injury history |
| Celeste | First PM check-in with skincare data OR first time she gives advice | Full product list (AM + PM), ingredient sensitivities, tret history and tolerance, SPF habits, skin photo request |
| Sage | First AM check-in with anxiety ≥ 6 OR first time stress is flagged | Anxiety history, what helps, what makes it worse, experience with NSDR/meditation/breathwork, therapy status |
| Aurore | Day 3–5 if missing data | Cycle info, supplements, medications not yet captured, anything the other agents flagged as missing |

### Implementation

Each deep-dive is a mini Council Round (triggered_by: `domain_onboarding`) where the specific agent asks 2–3 targeted questions. Responses are extracted and merged into UserProfile. New goals may be created from the conversation.

The `onboarding_layer` field on UserProfile increments to 2 once all Phase 1 agents have completed their deep-dive, and to 3 once integrations are connected.

---

## Layer 3: Integration Connections

Prompted via dashboard cards (not during onboarding flow):

### Whoop Connection Card
```
┌────────────────────────────────────────────────┐
│ ⌚ Connect Whoop                                │
│ Recovery-aware training, sleep tracking,        │
│ and smarter Council advice.                     │
│                                    [Connect →]  │
└────────────────────────────────────────────────┘
```
Tapping initiates OAuth flow. On success, first WhoopSnapshot is fetched and Rex immediately references it.

### Progress Photo Card
```
┌────────────────────────────────────────────────┐
│ 📸 Take your first progress photo              │
│ Rex uses these to track body composition        │
│ changes over time.                              │
│                                    [Let's go →] │
└────────────────────────────────────────────────┘
```

These cards disappear once the integration is connected / first photo is taken.

---

## Goal Integration with the Broader System

### In Council Rounds
Agents receive active goals in their round context:
```
--- ACTIVE GOALS ---
  [FOCUS] Build hourglass physique (Rex) — milestone: reach 58kg by June (current: 61.2kg)
  [FOCUS] Reduce anxiety baseline (Sage) — milestone: avg anxiety < 5 for a month (current avg: 6.1)
  [ACTIVE] Build tret tolerance (Celeste) — milestone: every other night by April
```

Agents are instructed: "Reference active goals when your advice connects to them. If progress is being made, acknowledge it. If a recommendation conflicts with a goal, explain the trade-off."

### In Pattern Detection
The pattern detection engine can check goal-relevant metrics:
- `GoalProgressDetector` — tracks current_value against target_value. Surfaces when milestones are close ("2kg away from your target"), achieved, or stalling.
- `GoalConflictDetector` — flags when behaviour patterns contradict stated goals (e.g. training frequency declining when the goal is 4x/week consistency).

### On the Dashboard
A "Goals" section (below streaks, above weekly summary) shows focus goals with progress indicators:
```
┌────────────────────────────────────────────────┐
│ 🎯 Focus Goals                                 │
│                                                 │
│ Reach 58kg by June          61.2 → 58.0 ██░░░ │
│ Avg anxiety < 5 this month  current avg: 6.1   │
│ Tret every other night      currently: every 6d │
└────────────────────────────────────────────────┘
```

### Monthly Goal Review
Aurore triggers a goal review round (triggered_by: `goal_review`) monthly:
- Shows current goals with progress
- Asks: "What still feels right? Anything shifted?"
- Allows reprioritising, pausing, or adding new goals
- Agents can propose new milestones based on observed progress

---

## Re-Onboarding / Profile Refresh

Accessible from Settings. Aurore walks through the same topics but shows current values and asks what's changed. Not a full re-do — just an update pass.

Also triggered proactively if:
- 30+ days since last profile review AND significant pattern shifts detected
- A new agent is activated (Phase 2 agents need their own deep-dive data)
- User explicitly asks to update their profile or goals

---

## Edge Cases

### User gives minimal responses
If extraction returns mostly nulls (confidence < 0.5), Aurore asks one targeted follow-up rather than moving on with empty data. "I want to make sure the Council has enough to work with — can you tell me a bit more about [specific gap]?"

### User wants to skip onboarding
Allow it, but with consequences. If onboarding is skipped, agents operate in "getting to know you" mode — their first few rounds include more questions and less advice. The dashboard shows a persistent "Complete your profile" card until Layer 1 is done.

### User changes their mind about goals
Goals can be edited or abandoned at any time with zero judgment. Abandoned goals are soft-deleted (status: abandoned) and don't appear in active views but remain in history for pattern analysis. No agent should ever say "but you said you wanted X" in a guilt-inducing way.

### Profile conflicts with data
If Shay says her training frequency is 5x/week but the data shows 3x/week consistently, Rex can gently surface this: "Your goal is 5 sessions a week, but you've been averaging 3 lately. Want to adjust the target or talk about what's getting in the way?" This is honest, not judgmental.
