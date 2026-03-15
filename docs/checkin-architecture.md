# Check-in System Architecture

**Date:** 2026-03-15
**Status:** Design sketch — to be implemented in sub-project 4
**Depends on:** Council Round Architecture, Whoop integration (sub-project 6 or minimal snapshot)

---

## Overview

The twice-daily check-in is the heartbeat of Aura. It must be effortless or it won't happen consistently. The system supports two modes — **conversational** (default, natural language parsed by Claude) and **quick-tap** (fallback, direct value selection) — both producing the same structured data and triggering a Council Round.

---

## Design Principles

1. **Don't ask for data the system already has.** Whoop sleep/recovery data is pre-populated, not re-entered.
2. **Conversational by default, structured as fallback.** Type "tired and anxious" → get parsed values to confirm. Or tap emoji scales directly.
3. **Confirm before saving.** Extraction is a preview, not a commitment. User always adjusts before anything is locked in.
4. **Council response is the reward.** After confirming, agent responses appear immediately — this reinforces the habit.
5. **Something is better than nothing.** Quick-tap mode captures less nuance but ensures data continuity on low-energy days.

---

## Three-Step API Flow

### Step 1 — Pre-populate
```
GET /checkin/prepopulate/am
GET /checkin/prepopulate/pm
```
Fetches context the system already knows:
- **AM:** Whoop sleep duration, recovery %, HRV, previous evening's rating/proud-of
- **PM:** Whoop strain, workout logged (from Workout model), skincare logged (from SkinRoutine), today's tasks with completion status, morning check-in values for continuity

This data is displayed as a header — not as input fields.

### Step 2 — Extract (conversational mode only)
```
POST /checkin/extract/am
POST /checkin/extract/pm
Body: { raw_input: "Tired and anxious. Didn't sleep well." }
```
Lightweight Claude API call (NOT a Council Round) that parses natural language into structured values. Returns:
- Extracted values (energy, mood, anxiety, etc.)
- Confidence score (below 0.7 → suggest manual adjustment)
- Missing fields list
- Follow-up question if a key field wasn't mentioned (e.g. "What's one thing you want to focus on today?")

Quick-tap mode bypasses this step entirely.

### Step 3 — Confirm + Save + Trigger Round
```
POST /checkin/confirm
Body: { checkin_type, date, energy, mood, anxiety, ... , mode, raw_input }
```
Saves the confirmed values, updates habit streaks, and triggers a Council Round. Returns the round's user-facing messages immediately.

---

## Morning Check-in Fields

| Field | Type | Source | Required |
|---|---|---|---|
| `energy` | 1–10 | User input | Yes |
| `mood` | 1–10 | User input | Yes |
| `anxiety` | 1–10 | User input | Yes |
| `sleep_notes` | Text | User input (optional) | No |
| `intention` | Text | User input (optional) | No |
| `whoop_recovery` | Float | Auto-snapshotted | No |
| `whoop_hrv` | Float | Auto-snapshotted | No |
| `whoop_sleep_score` | Float | Auto-snapshotted | No |
| `raw_input` | Text | Stored from conversational mode | No |
| `mode` | Enum | `conversational`, `quick_tap`, `backfill` | Yes |

## Evening Check-in Fields

| Field | Type | Source | Required |
|---|---|---|---|
| `day_rating` | 1–10 | User input | Yes |
| `skincare_done` | Boolean | Auto-detected from SkinRoutine, user-correctable | Yes |
| `proud_of` | Text | User input | No |
| `council_flag` | Text | User input (anything to flag for The Council) | No |
| `tasks_completed` | JSON | Auto-populated from task tracking, user-correctable | No |
| `whoop_strain` | Float | Auto-snapshotted | No |
| `raw_input` | Text | Stored from conversational mode | No |
| `mode` | Enum | Same as AM | Yes |

---

## Conversational Extraction

The extraction uses a tightly constrained Claude system prompt that outputs only JSON. It maps natural language to the 1–10 scale:

- "Tired" ≈ 3–4. "Good" ≈ 6–7. "Great" ≈ 8–9. "Awful" ≈ 1–2.
- Stress maps to anxiety. Sleep quality maps to both energy context and sleep_notes.
- If a field isn't mentioned → null + listed in `missing_fields`
- Confidence: direct numbers → 0.95, clear descriptors → 0.8, vague/minimal → 0.6

---

## Quick-Tap Mode

For low-energy days. Collapses the check-in to bare minimum:

**Morning:** Three emoji-scale rows (energy, mood, anxiety — 5 faces each) + optional one-line intention. ~10 seconds.

**Evening:** One day rating (emoji scale) + skincare yes/no toggle + optional one-line "proud of." ~8 seconds.

User preference for conversational vs quick-tap stored in localStorage. Toggle visible at top of check-in screen.

---

## Frontend Component Structure

```
CheckInPage.tsx                    — Route: /checkin. Determines AM/PM, manages state machine.
├── CheckInHeader.tsx              — Shows Whoop context (pre-populated, not editable)
├── ConversationalInput.tsx        — Aurore's prompt + text area + submit
├── QuickTapInput.tsx              — Emoji-scale rows + optional text fields
├── ExtractionConfirmation.tsx     — Parsed values as tappable/adjustable pills
├── CouncilResponsePanel.tsx       — Streams agent responses after confirmation
├── ModeToggle.tsx                 — "Talk to Aurore" / "Quick tap" switch
└── BackfillBanner.tsx             — "Missed yesterday? Quick backfill?"
```

### State Machine

```
IDLE → PREPOPULATING → INPUT → EXTRACTING (conversational only)
→ CONFIRMING → SAVING → COUNCIL_RESPONDING → COMPLETE
```

---

## Backfill Support

If the previous day's check-in was missed:
- A banner appears: "You missed yesterday's evening check-in. Quick backfill?"
- Opens a simplified version for yesterday's date
- Backfills do NOT trigger Council Rounds (data is for trend analysis only)
- Values saved with `mode: backfill`

---

## Streak Integration

After saving a check-in, the confirm endpoint updates `HabitStreak` records:
- `Check-ins` streak: incremented if last_completed == yesterday, reset if gap
- `Skincare` streak (PM only): updated if skincare_done == true
- `Training` streak: updated separately when Workout records are logged

Streak ownership: Rex → Training, Celeste → Skincare, Sage → Check-ins + NSDR.

---

## Smart Notification Timing (Phase 2+)

Design now, implement later:
- **Morning prompt:** ~5 min after Whoop-detected wake time. Fallback: 7:00 AM.
- **Evening prompt:** ~30 min before average bedtime (from Whoop). Fallback: 9:00 PM.
- **Missed check-in nudge:** If AM not done by 12:00 PM, Sage sends a casual message in Council Chat (proactive round, not notification).
- **Adaptive:** Track which prompt times get fastest response, gradually adjust.
