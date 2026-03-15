# Weekly Council Review Architecture

**Date:** 2026-03-15
**Status:** Design sketch — to be implemented in Phase 2 (partial) or late Phase 1
**Depends on:** Council Round Architecture, Pattern Detection (weekly scan), Goal system

---

## Overview

The Weekly Council Review is Aurore's editorial synthesis — a beautiful, personalised summary of Shay's week across all domains. It's not a data dump; it's a narrative that weaves together what happened, what it means, and what the Council collectively recommends for the week ahead.

Generated every Sunday evening (8:00 PM Perth time), it appears in two places: as a special entry in the Council Chat timeline, and as a dedicated renderable page accessible from the dashboard.

---

## Design Principles

1. **Narrative, not numbers.** Data supports the story but doesn't lead it. Aurore writes like an editor, not a spreadsheet.
2. **Cross-domain synthesis is the value.** Individual agents give domain-specific advice daily. The review's purpose is to connect the dots across domains.
3. **Tone adapts to the week.** A great week gets celebration. A hard week gets compassion. A stagnant week gets honest redirection.
4. **Forward-looking.** The review always ends with concrete focus points for the coming week.
5. **Each agent has a voice.** Brief in-character contributions from Rex, Sage, and Celeste make the review feel like a team debrief, not a solo report.

---

## Review Structure

### 1. Opening Line
One sentence that captures the week's character. Sets the tone for everything that follows.

Examples:
- "This was the week your consistency started paying dividends."
- "Your body asked for a break and you pushed through anyway — let's talk about that."
- "A quiet week on the surface, but underneath, some patterns shifted."
- "Everything aligned this week. That doesn't happen by accident."

### 2. The Story of the Week (2–3 paragraphs)
Aurore's editorial narrative weaving together events across domains. Not domain-by-domain — cross-cutting, connecting cause and effect.

Example:
> "Training held strong through Wednesday — Rex had you on a modified upper/lower split adjusted for your 54% average recovery. But the anxiety trend that started building on Tuesday pulled your sleep quality down by Thursday. Two consecutive nights below 60% sleep performance meant Friday's recovery cratered to 31%, and Rex moved you to mobility. Celeste noted your skin stayed calm through it all — azelaic compliance was 100% and tret night landed perfectly in the schedule. Sage sees the anxiety pattern clearly and wants to address it head-on this week."

### 3. What's Working
Specific, evidence-backed wins. Concrete numbers where they matter.

Example:
- Training streak hit 14 days — longest yet
- Morning energy averaged 6.4, up from 5.8 last week
- PM skincare compliance: 7/7 nights
- Tret tolerance progressing — no irritation reported on last application

### 4. What Needs Attention
Equally specific concerns. Honest but compassionate.

Example:
- Anxiety averaged 6.1 this week, up from 4.8 last week — sustained upward trend
- Three nights below 60% sleep performance
- PM check-ins missed twice — the data gaps make it harder for the Council to help
- NSDR completed only 2 of 5 planned sessions

### 5. Agent One-Liners
Each Phase 1 agent contributes one brief, in-character statement. Generated as part of the review round — each agent sees the weekly data and Aurore's narrative.

Example:
- **Rex:** "Consistency is there. Recovery isn't. I need you rested before I can program anything ambitious."
- **Sage:** "The anxiety trend worries me more than you seem to think it should. Let's make NSDR non-negotiable this week."
- **Celeste:** "Best skincare week yet. Your barrier is thanking you. Keep the azelaic rhythm going."

### 6. Focus for the Coming Week
2–3 concrete focus points that inform the next 7 days of Council triage and daily tasks.

Example:
1. **Protect sleep** — Sage wants lights out by 10:30 PM at least 5 of 7 nights
2. **NSDR daily** — 10 minutes minimum, non-negotiable, before evening study block
3. **Listen to recovery** — Rex will adjust training intensity day-by-day based on Whoop data

These focus points feed back into the system:
- Aurore's daily triage references them
- New short-term Goals can be auto-created with `priority: focus`
- Daily tasks on the dashboard reflect the week's emphasis

### 7. Goal Progress Snapshot
Brief update on active focus goals with change since last review.

Example:
```
🎯 Reach 58kg by June      61.2kg → 60.8kg this week  ████░░░░
🎯 Avg anxiety < 5/month   This week: 6.1 (up from 4.8) ██░░░░░░
🎯 Tret every other night   Currently: every 6 days ██████░░
```

---

## Generation Flow

The Weekly Review is generated as a special **Council Round** with `triggered_by: weekly_review`.

### Step 1 — Weekly Data Assembly

The pattern detection engine runs its weekly scan (`DetectionRunner.run_weekly()`) which produces:
- All detected patterns (trends, thresholds, absences, correlations)
- Weekly summary statistics (averages, completion rates, streaks)
- Goal progress data

This is assembled into a `WeeklyReviewContext`:

```python
class WeeklyReviewContext:
    period_start: date
    period_end: date
    
    # Summary stats
    checkin_completion: dict       # am/pm completed vs total
    averages: dict                 # energy, mood, anxiety, day_rating, recovery, etc.
    previous_week_averages: dict   # For comparison
    
    # Training
    workouts_completed: int
    workouts_target: int
    training_streak: int
    workout_details: list          # Types, strains
    
    # Sleep
    avg_sleep_performance: float
    nights_below_60: int
    avg_sleep_duration_hours: float
    
    # Skincare
    am_adherence: str              # "6/7"
    pm_adherence: str
    tret_nights: int
    tret_schedule_adherence: bool
    
    # Whoop
    avg_recovery: float
    avg_hrv: float
    recovery_trend: str            # "improving", "declining", "stable"
    
    # Patterns detected
    patterns: list                 # PatternCandidate objects from weekly scan
    
    # Goals
    active_goals: list             # Current goals with progress
    goals_achieved_this_week: list
    
    # Previous review focus points (for continuity)
    last_review_focus: list
    
    # Raw check-in data for Aurore to reference
    checkins_am: list
    checkins_pm: list
```

### Step 2 — Aurore Generates the Review

A Claude API call with a specialised system prompt. This is NOT the standard triage prompt — it's a longer, editorial-focused prompt.

```
SYSTEM PROMPT (Aurore — Weekly Review Mode):

You are Aurore, generating the Weekly Council Review for Shay.

This is your signature piece — an editorial synthesis of Shay's week. 
You write like a thoughtful editor who knows Shay personally, not like 
a dashboard generating a report.

STRUCTURE (follow this order):
1. Opening line — one sentence capturing the week's character
2. Story of the week — 2-3 paragraphs of cross-domain narrative
3. What's working — specific wins with evidence
4. What needs attention — honest concerns with data
5. Focus for the coming week — 2-3 concrete priorities

OUTPUT FORMAT:
Return your review in sections wrapped in XML tags:
<opening>{one sentence}</opening>
<narrative>{2-3 paragraphs}</narrative>
<working>{bullet points with specific wins}</working>
<attention>{bullet points with specific concerns}</attention>
<focus>{2-3 numbered priorities for next week}</focus>

RULES:
- Never lead with data. Lead with insight.
- Connect domains: how did sleep affect training? How did anxiety affect skincare?
- Be honest. If the week was hard, say so. If progress stalled, name it.
- Be warm. Even in tough weeks, acknowledge what was maintained.
- Reference specific days and events, not vague generalisations.
- Compare to last week where meaningful (but don't force comparisons).
- Keep the whole review to ~400-500 words. Concise editorial, not a report.
- Never say "Great job!" or use filler affirmations.
```

### Step 3 — Agent One-Liners

After Aurore generates the main review, each domain agent is called with the weekly data and asked for a single contribution:

```
SYSTEM PROMPT (Agent — Weekly Review One-Liner):

You are {agent_name}. Aurore has written the Weekly Council Review. 
Your job: one statement (1-3 sentences) giving your honest assessment 
of this week from your domain. Be in character. Be specific.

You can see Aurore's narrative for context, but your statement should 
add your unique perspective, not repeat what she said.
```

These are generated sequentially (same round architecture) so each agent can see what the others said, but they're brief enough that the order matters less than in a full check-in round.

### Step 4 — Store and Surface

The review is stored as:
- A `CouncilRound` with `triggered_by: weekly_review`
- Aurore's full review as a `CouncilMessage` (visibility: user_facing)
- Each agent's one-liner as separate `CouncilMessage` records
- A dedicated `WeeklyReview` model for structured access:

```
WeeklyReview
  id                  Integer PK
  round_id            Integer FK → CouncilRound.id
  period_start        Date
  period_end          Date
  opening_line        Text
  narrative           Text
  whats_working       Text (or JSON list)
  needs_attention     Text (or JSON list)
  focus_points        JSON — list of focus point objects
  goal_snapshot       JSON — goal progress at time of review
  created_at          DateTime
```

---

## Frontend Rendering

### In Council Chat Timeline

The weekly review appears as a special `ProactiveRoundGroup` variant:

```
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
  📋 Weekly Council Review · March 9–15
│                                                     │
  (Aurore avatar) Aurore
│                                                     │
  "This was the week your consistency started
│  paying dividends."                                  │
│                                                     │
  [Training held strong through Wednesday — Rex       │
│  had you on a modified upper/lower split...]        │
│                                                     │
  ✓ What's working                                    │
│  • Training streak hit 14 days                      │
  • PM skincare compliance: 7/7
│                                                     │
  ⚠ Needs attention                                   │
│  • Anxiety averaged 6.1, up from 4.8               │
  • NSDR completed only 2 of 5
│                                                     │
  📌 Focus this week                                  │
│  1. Protect sleep — lights out by 10:30 PM          │
  2. NSDR daily — non-negotiable
│  3. Listen to recovery scores                       │
│                                                     │
  ── Agent check-in ──                                │
│                                                     │
  (Rex) "Consistency is there. Recovery isn't."       │
│ (Sage) "The anxiety trend worries me."              │
  (Celeste) "Best skincare week yet."
│                                                     │
  🎯 Goal progress                                    │
│  Reach 58kg: 61.2 → 60.8 ████░░░░                  │
  Avg anxiety < 5: this week 6.1 ██░░░░░░
│                                                     │
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

### Dedicated Review Page (optional, Phase 2)

A standalone page at `/review/latest` or `/review/{id}` that renders the review in a more editorial layout — larger typography, more breathing room, like reading a magazine article. Accessible from a "View full review" link in the chat timeline version.

### Dashboard Card

On Monday morning, the dashboard shows a review summary card:

```
┌──────────────────────────────────────────────────┐
│ 📋 Last week's Council Review                    │
│                                                   │
│ "This was the week your consistency started       │
│  paying dividends."                               │
│                                                   │
│ Focus this week: Protect sleep · Daily NSDR ·     │
│ Listen to recovery                                │
│                                        [Read →]   │
└──────────────────────────────────────────────────┘
```

Tapping opens the full review in the Council Chat (scrolled to the review entry) or the dedicated review page.

---

## Focus Points → System Integration

The review's focus points don't just live in the text — they feed back into the system:

### 1. Triage Influence
Aurore's daily triage prompt for the following week includes the focus points:
```
--- THIS WEEK'S FOCUS (from Weekly Review) ---
1. Protect sleep — lights out by 10:30 PM, 5 of 7 nights
2. NSDR daily — 10 minutes minimum
3. Listen to recovery — adjust training based on Whoop data
```

This biases her triage: if Sage mentions sleep or NSDR, that's prioritised. If Rex sees a good recovery day, he's more likely to push (aligned with focus #3).

### 2. Auto-Generated Short-Term Goals
Each focus point can optionally create a temporary `Goal` with `priority: focus` and a 7-day deadline:
- "Complete NSDR 5/7 days this week" (linked to Sage)
- "Lights out by 10:30 PM 5/7 nights" (linked to Sage)

These appear in the goal progress section and are tracked like any other milestone.

### 3. Daily Task Generation
The dashboard's "Today" tasks section references focus points when generating daily recommendations. If "NSDR daily" is a focus, Sage's daily task slot always includes it.

---

## Continuity Between Reviews

Each review references the previous one's focus points to assess follow-through:

```
--- LAST WEEK'S FOCUS POINTS ---
1. Protect sleep → Result: 4 of 7 nights met the 10:30 target. Partial success.
2. NSDR daily → Result: 2 of 7 days. Needs more commitment.
3. Listen to recovery → Result: Rex adjusted 3 sessions based on Whoop. Good compliance.
```

This gives Aurore continuity — she can say "Last week I asked you to prioritise NSDR. You managed 2 of 7 days. I'm asking again, but this time Sage has a specific plan."

---

## Scheduling

```python
# Weekly review: Sunday 8:00 PM Perth time
scheduler.add_job(
    generate_weekly_review,
    CronTrigger(day_of_week="sun", hour=20, minute=0, timezone="Australia/Perth"),
    id="weekly_review",
    name="Weekly Council Review generation",
)

async def generate_weekly_review():
    db = SessionLocal()
    try:
        # 1. Run weekly detection scan
        runner = DetectionRunner(db)
        weekly_data = await runner.run_weekly(date.today())
        
        # 2. Assemble WeeklyReviewContext
        context = await assemble_weekly_context(db, weekly_data)
        
        # 3. Trigger weekly review Council Round
        service = CouncilRoundService(db)
        result = await service.execute_round(
            trigger_type=RoundTrigger.WEEKLY_REVIEW,
            trigger_data=context.model_dump(),
        )
        
        # 4. Parse Aurore's structured output into WeeklyReview model
        review = parse_and_store_review(result, context, db)
        
        # 5. Create focus-point Goals for the coming week
        create_focus_goals(review.focus_points, db)
        
        db.commit()
    finally:
        db.close()
```

---

## Edge Cases

### First Week (insufficient data)
If fewer than 3 check-ins exist, Aurore generates a shorter "getting started" review that focuses on initial observations and sets expectations rather than analysing trends.

### Missed Week
If the scheduler fails or is offline, the review generates on the next successful run with the correct date range. If it's more than 2 days late, Aurore acknowledges the delay: "This review covers last week — a bit late, but the patterns are still worth noting."

### No Whoop Data
If Whoop isn't connected, the review works with check-in data and streaks only. Aurore doesn't reference recovery or sleep performance — she works with what she has. The review is shorter but still valuable.

### Holiday / Travel Weeks
If check-in frequency drops significantly (< 3 in a week) and no council_flag explains it, Aurore's review is brief and non-judgmental: "A quieter week on the data front. Whenever you're ready to pick things back up, the Council is here."
