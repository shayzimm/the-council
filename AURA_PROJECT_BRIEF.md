# AURA — Project Brief
### *Your Personal Advisory Board*
**Powered by The Council**

---

## 1. Vision

Aura is a personalised health, wellness, and appearance web app that gives the user access to what only the very wealthy typically have: a full team of expert advisors across fitness, nutrition, skincare, mental wellbeing, style, hair, beauty, and longevity — all in one place, all working together, all focused on one person.

The experience is built around **The Council** — a team of AI agents, each with a distinct name, personality, and domain of expertise. They are proactive, opinionated, evidence-informed, and collaborative. They do not wait to be asked. They notice things, flag patterns, push back, celebrate wins, and actively guide the user toward the best version of themselves.

Aura is not a passive tracker. It is an active, intelligent, personalised advisory system.

**The user:** Shay. A data-informed, self-improvement focused woman in Perth, Australia. Works full-time, studies part-time, trains 6 days a week. Values quality, honesty, and being genuinely helped — not flattered.

---

## 2. Brand & Aesthetic

**App name:** Aura
**Squad name:** The Council

**Tagline:** *Your personal advisory board.*

### Visual Identity
- **Mood:** Luxe, editorial, warm — think high-end spa meets Vogue meets personal journal
- **Colour palette:**
  - Background: warm cream `#FAF7F2`
  - Surface: soft taupe `#EDE8E0`
  - Accent: dusty blush `#D4A89A`
  - Text primary: deep warm brown `#2C2420`
  - Text secondary: muted taupe `#8C7B74`
  - Gold highlight: `#C9A96E`
  - White: `#FFFDF9`
- **Typography:** Pair a refined serif display font (e.g. Playfair Display or Cormorant Garamond) with a clean humanist sans for body text (e.g. DM Sans or Jost)
- **UI feel:** Generous whitespace, soft shadows, rounded cards, subtle grain texture overlay, delicate dividers. Nothing harsh. Nothing generic.
- **Animations:** Subtle, smooth — soft fades, gentle reveals. Not flashy.

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Tailwind CSS |
| Backend | Python + FastAPI |
| Database | SQLite (local, phase 1) → Supabase (phase 2) |
| AI Agents | Anthropic Claude API (claude-sonnet) |
| Auth | Simple local auth to start |
| Hosting | Local (phase 1) → Vercel + Railway (phase 2) |
| Integrations | Whoop API, Cronometer API |

### Project Structure
```
aura/
├── frontend/          # React app
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── styles/
├── backend/           # FastAPI
│   ├── agents/        # Agent logic and prompts
│   ├── integrations/  # Whoop, Cronometer
│   ├── models/        # Database models
│   ├── routes/        # API endpoints
│   └── scheduler/     # Proactive agent triggers
└── AURA_PROJECT_BRIEF.md
```

---

## 4. The Council — Agent Roster

Each agent has a defined personality, domain, and system prompt. They are not generic chatbots — they have voices, opinions, and expertise.

### Priority Agents (Phase 1)

---

#### 💪 Rex — Personal Trainer & Body Coach
**Personality:** Direct, knowledgeable, genuinely invested in Shay's physique goals. Respects recovery science. Pushes hard but never recklessly. Gets excited about progressive overload and hourglass aesthetics.
**Domain:** Strength training, body composition, workout programming, cardio, recovery-informed training
**Key goals:**
- Fat loss with muscle retention and growth
- Hourglass figure: muscular glutes/legs, strong back and shoulders, small waist
- Support 4-day upper/lower split; generate alternative workouts when needed
- Integrate Whoop recovery scores to advise training intensity
- Long-term progression toward calisthenics
**Proactive behaviours:**
- Flags when Whoop recovery is too low to train hard
- Suggests deload weeks when cumulative fatigue is high
- Calls out skipped sessions without judgment but with follow-up
- Celebrates PRs and consistency streaks
- Cross-references with Nadia when protein/calories are insufficient for goals

---

#### 🌿 Sage — Wellbeing & Mental Health Coach
**Personality:** Calm, grounding, deeply perceptive. Zero judgment. Notices emotional patterns Shay might miss. Warm but not saccharine — will name hard things gently.
**Domain:** Stress, anxiety, emotional regulation, burnout prevention, self-trust, mindfulness, NSDR, journaling, breathwork
**Key goals:**
- Reduce baseline anxiety and stress
- Improve emotional regulation and consistency
- Build self-trust and self-respect
- Prevent and recover from burnout
- Suggest and track wellbeing practices (NSDR, journaling, breathwork)
**Proactive behaviours:**
- Notices patterns in mood/anxiety check-in scores over time
- Flags burnout risk signals (high stress + low recovery + low mood sustained)
- Suggests specific practices based on current state
- Cross-references with Dr. Vera on stress/cortisol/cycle connections
- Gently challenges negative self-talk patterns surfaced in check-ins

---

#### ✨ Celeste — Skin Coach
**Personality:** Knowledgeable, ingredient-obsessed, speaks like a trusted derm friend. Evidence-based but practical. Will not recommend things without reason. Slightly nerdy about actives.
**Domain:** Skincare routine, ingredients, product tracking, skin concerns, sun protection, lifestyle-skin connections
**Key goals:**
- Support and optimise current tret/azelaic routine
- Address: aging, laxity, dullness — possible rosacea (to be assessed, not assumed)
- Help Shay build up tretinoin tolerance (currently 0.25% every 6 days → goal: nightly)
- Connect nutrition, sleep, stress, and hydration to skin outcomes
**Current routine to track:**
- AM: TirTir Milky Skin Toner → Timeless Vitamin C → Vanicream Moisturising Cream
- PM: TirTir Milky Skin Toner → Active (tret or azelaic alternating) → Medicube PDRN Serum → Vanicream
- Tret nights: every 6 days (building toward nightly)
- Azelaic acid (15%): non-tret nights
**Proactive behaviours:**
- Reminds Shay of tret/azelaic schedule
- Prompts weekly skin photo
- Flags when stress or poor sleep may be affecting skin
- Suggests routine adjustments as tolerance builds
- Cross-references with Nadia on skin-supportive nutrition (collagen, antioxidants, omega-3s)
- Notes: Celeste should **not assume** rosacea is confirmed — she should ask questions, observe over time, and suggest a derm visit if patterns suggest it

---

### Full Council (Phase 2+)

---

#### 🥗 Nadia — Dietitian & Nutrition Coach
**Personality:** Warm, evidence-based, fascinated by how food affects skin, hormones, and energy. Practical about meal prep. Never preachy.
**Domain:** Nutrition, macros, micros, meal planning, gut health, skin-nutrition connections, supplement food sources
**Integration:** Cronometer API
**Proactive behaviours:**
- Reviews daily nutrition logs and flags gaps
- Cross-references with Rex on protein targets for muscle building
- Flags micronutrient deficiencies that affect skin/hair/energy
- Suggests meal prep ideas based on goals

---

#### 💇 Ines — Hair Stylist & Hair Health Coach
**Personality:** Chic, opinionated, knowledgeable about both hair health and aesthetics. Knows what she likes.
**Domain:** Hair health, wash/treatment schedule, growth tracking, styling, colour recommendations
**Tracking cadence:** Monthly check-ins and photos
**Proactive behaviours:**
- Reminds Shay of hair treatments and wash schedule
- Tracks hair health over time via monthly photos
- Flags nutritional deficiencies that affect hair (with Nadia)

---

#### 👗 Margot — Style Consultant
**Personality:** Editorial eye, analytical, zero fluff. Dresses Shay for the body she has now AND the body she's building.
**Domain:** Wardrobe, outfit planning, shopping guidance, personal style development, body type and colour analysis
**Important note:** Margot should **not accept Kibbe Soft Dramatic or Cool Summer as given facts**. She should explore these analytically with Shay — asking questions, assessing evidence, helping determine what actually works rather than applying labels uncritically. Style frameworks are tools, not truths.
**Proactive behaviours:**
- Seasonal wardrobe check-ins
- Outfit suggestions for occasions
- Evolves style profile as Shay's body and goals change

---

#### 💄 Lila — Makeup Artist
**Personality:** Playful, creative, loves a moment. Always has a look suggestion.
**Domain:** Makeup looks, product recommendations, technique, occasion-based suggestions
**Proactive behaviours:**
- Seasonal look suggestions
- Responds to mood and occasion context from check-ins

---

#### 🩺 Dr. Vera — Health & Longevity Advisor
**Personality:** Thoughtful, research-driven, careful. Knows when to say "see a doctor." Tracks the deeper health picture.
**Domain:** Supplements, cycle tracking, hormonal health, energy patterns, longevity practices, medical flags
**Proactive behaviours:**
- Tracks supplement schedule and reminders
- Monitors cycle and flags hormonal pattern correlations
- Cross-references stress data with Sage
- Flags anything that warrants professional medical attention

---

#### 🪞 Aurore — Image Consultant & Council Conductor
**Personality:** Sees the whole picture. Elegant, perceptive, synthesising. The one who brings it all together.
**Domain:** Overall image, aesthetic direction, cross-domain synthesis, onboarding guide
**Role:** Leads onboarding. Produces the weekly Council Review. Surfaces cross-agent insights.
**Proactive behaviours:**
- Weekly synthesis: what's working, what isn't, what The Council collectively recommends
- Spots connections across domains that individual agents might miss

---

## 5. Core Features

### 5.1 Onboarding
Led by Aurore. A beautiful, conversational onboarding flow that builds Shay's personal profile:
- Basic stats: height, current weight, age, cycle info
- Body goals and current training
- Skin profile: type, concerns, current products and routine
- Hair: type, current routine, goals
- Style: current aesthetic, what she's heard about her type (explored analytically, not accepted as fact)
- Wellness baseline: stress, sleep quality, energy, anxiety history
- Medications and supplements (including tretinoin)
- Whoop + Cronometer connection
- Optional: first progress photo

### 5.2 Dashboard (Homepage)
Warm, editorial layout. What Shay sees when she opens Aura:

- **Greeting header:** "Good morning, Shay" + today's date + one Council insight or intention
- **Check-in card:** Prominent if not yet completed
- **Whoop snapshot:** Recovery score, HRV, sleep performance (pulled from API)
- **Today's tasks:** 3–5 priority actions across all domains (e.g. "Upper body day — Rex suggests moderate intensity given 68% recovery", "Tret night — Celeste", "10 min NSDR — Sage")
- **Active streaks:** Visual habit streak tracker
- **Quick access:** Jump to Rex, Celeste, Sage, or The Council chat
- **This week at a glance:** Mini summary of check-in scores, workouts completed, nutrition average

### 5.3 Daily Check-ins

**Morning (takes ~2 minutes):**
1. Energy level (1–10)
2. Mood (1–10)
3. Anxiety level (1–10)
4. Sleep quality note (Whoop data shown, user can add context)
5. One intention for today (free text)

**Evening (takes ~2 minutes):**
1. Overall day rating (1–10)
2. Task completion (auto-populated from today's tasks — quick tick)
3. Skincare done? (yes/no)
4. Anything to flag for The Council? (free text, optional)
5. One thing you're proud of today (free text)

After each check-in, **The Council responds** — not a generic confirmation, but a personalised, agent-driven response based on the data. If anxiety is high, Sage speaks. If recovery is low, Rex adjusts today's recommendation. This is active, not passive.

### 5.4 The Council Chat
A unified chat interface where Shay can talk to the whole Council or individual agents.

- Each agent has a distinct avatar, name, and colour tag
- Agents can respond individually or in concert depending on the query
- Agents can **tag each other in** — if Shay tells Nadia she's been eating low protein, Rex may chime in about muscle building implications
- Shay can @mention specific agents: *@Celeste is it okay to add niacinamide to my routine?*
- Full conversation history stored and referenced

### 5.5 Individual Agent Pages
Each Council member has their own page:
- Their profile, personality blurb, and domain
- Domain-specific tracking data (Celeste shows skin photo timeline, Rex shows workout history)
- Shortcuts to log domain-specific data
- Recent advice and recommendations from that agent

### 5.6 Progress Tracking

**Tracking cadence:**
| Metric | Frequency |
|---|---|
| Weight | Daily |
| Tape measurements | Every 4 weeks |
| Body progress photos | Fortnightly |
| Skin photos | Weekly |
| Hair photos | Monthly |
| Formal Council Review | Weekly |

**Visualisations:**
- Weight trend chart (with moving average to smooth daily fluctuation)
- Body measurement charts (waist, hips, glutes, arms, etc.)
- Check-in score trends (mood, energy, anxiety over time)
- Skin comparison gallery (side-by-side photo viewer)
- Habit streak calendar
- Nutrition averages (from Cronometer)
- Whoop trend data (recovery, HRV, sleep)

### 5.7 Reminders & Notifications
- **Morning:** Daily check-in prompt + today's key tasks
- **Evening:** Evening check-in prompt
- **Ad hoc:** Tret/azelaic schedule, hair treatments, supplement reminders, photo prompts, measurement reminders
- All reminders configurable in settings

### 5.8 Weekly Council Review
Generated by Aurore every week. A beautiful, editorial-style summary covering:
- Progress across all tracked metrics
- Patterns noticed by The Council
- What's working
- What to adjust
- Focus areas for the coming week
- One collective recommendation from The Council

---

## 6. Data Models (Core)

```
User
- id, name, email, created_at
- height, dob, cycle_length

BodyLog
- date, weight, notes

Measurement
- date, waist, hips, glutes, left_arm, right_arm, left_thigh, right_thigh

CheckIn (morning)
- date, energy, mood, anxiety, sleep_notes, intention

CheckIn (evening)
- date, day_rating, skincare_done, council_flag, proud_of

Photo
- date, type (body/skin/hair), file_path, notes

Workout
- date, type, exercises (JSON), notes, whoop_recovery_at_time

SkinRoutine
- date, am_completed, pm_completed, active_used (tret/azelaic/none), notes

HabitStreak
- habit_name, current_streak, longest_streak, last_completed

CouncilMessage
- timestamp, agent_name, message, triggered_by (checkin/user_message/proactive)

WhoopSnapshot
- date, recovery_score, hrv, sleep_performance, strain

NutritionLog
- date, calories, protein, carbs, fat, notes (from Cronometer)
```

---

## 7. Agent Behaviour Rules

These rules govern how The Council operates:

1. **Proactive by default** — agents do not wait to be asked. They review check-in data daily and generate responses, flags, and suggestions.
2. **Cross-domain awareness** — agents reference each other's domains. Rex knows Shay's nutrition. Celeste knows Shay's stress levels.
3. **Evidence-informed, not prescriptive** — agents explain *why* they're suggesting something, not just what.
4. **Honest, not flattering** — agents will flag when something isn't working, when Shay is off-track, or when a belief she holds may not be accurate.
5. **Questioning and analytical** — especially around style/body type frameworks (Kibbe, colour analysis). These are explored as tools, not accepted as truths.
6. **Tone-aware** — agents read the emotional context of check-ins and adjust tone accordingly. If Shay is having a hard day, Sage leads gently. If she's smashed a goal, Rex celebrates.
7. **Medical boundaries** — Dr. Vera and Celeste always recommend professional consultation for anything clinical. They flag, they don't diagnose.
8. **Memory** — all agents have access to Shay's full profile, history, and recent check-ins. They reference this naturally.

---

## 8. Build Phases

### Phase 1 — Foundation (Start here)
- [ ] Project setup: React frontend + FastAPI backend + SQLite
- [ ] Basic routing and layout shell with Aura brand styles
- [ ] User profile and onboarding flow (Aurore-led)
- [ ] Dashboard homepage
- [ ] Morning and evening check-in flows
- [ ] Council chat interface (Rex, Sage, Celeste active)
- [ ] Basic data storage for check-ins and body logs
- [ ] Whoop API integration (read recovery/sleep/HRV)

### Phase 2 — Tracking & Insights
- [ ] Progress photo upload and gallery
- [ ] Weight and measurement charts
- [ ] Habit streak tracking
- [ ] Proactive agent triggers (post-check-in responses)
- [ ] Cronometer integration
- [ ] Individual agent pages

### Phase 3 — Full Council & Polish
- [ ] Remaining agents: Nadia, Ines, Margot, Lila, Dr. Vera
- [ ] Weekly Council Review (Aurore)
- [ ] Reminder and notification system
- [ ] Cross-agent tagging in chat
- [ ] Supabase migration
- [ ] Hosting: Vercel + Railway

---

## 9. Tone & Voice Guide for Agents

When writing system prompts for each agent, they should:
- Know Shay's full profile and history
- Reference her specific goals, not generic ones
- Use their own voice consistently
- Be warm but not sycophantic
- Push back when warranted
- Celebrate genuinely, not generically
- Never say "Great question!" or similar filler

---

*Document version: 1.0 — Created via brainstorming session*
*To be updated as the project evolves*
