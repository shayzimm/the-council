# Proactive Pattern Detection Architecture

**Date:** 2026-03-15
**Status:** Design sketch — to be implemented in sub-project 4–5 (post-check-in scan) and Phase 2 (nightly/weekly scans)
**Depends on:** Council Round Architecture, Check-in Architecture

---

## Overview

The pattern detection system lets the Council notice things before Shay does and speak up unprompted. It uses a **two-layer approach**: rule-based detectors generate candidate patterns, then Aurore (via Claude) filters candidates, assigns severity, and decides which agents respond.

This separation prevents alert fatigue — raw rules over-trigger, but Aurore applies judgment about what's noise and what's signal.

---

## Pattern Categories

| Category | Examples | Typical Agent |
|---|---|---|
| **Trend** | Anxiety rising 4→7 over 5 days, mood declining, recovery dropping week-over-week | Sage, Rex |
| **Threshold breach** | Recovery < 30%, anxiety ≥ 9, 3 consecutive gym skips | Rex, Sage |
| **Absence** | Check-in missed 2+ days, no workout in 5 days, tret night skipped | Sage, Rex, Celeste |
| **Cross-domain correlation** | Anxiety spikes after poor sleep, mood drops after skipped workouts | Aurore |
| **Streak at risk** | A 10+ day streak about to break (no data logged today, getting late) | Owning agent |
| **Streak milestone** | Hit 7, 14, 21, 30, 60, or 90 day streak | Owning agent |
| **Positive trend** | Mood averaging above 7 for 2 weeks, anxiety trending down | Sage, Aurore |
| **Composite (burnout)** | High anxiety + low mood + low energy + low recovery sustained 5+ days | Sage (primary), all agents |

---

## Detection Triggers

### 1. Post-Check-in Scan (synchronous, lightweight)
Runs after every check-in confirmation, BEFORE the Council Round fires. Detected patterns are injected into the round context so agents can reference them naturally.

Detectors: anxiety/mood/energy trends, recovery/anxiety thresholds, streak milestones.

### 2. Nightly Scheduled Scan (10:30 PM Perth time)
Catches things the post-check-in scan misses: absence patterns, cross-domain correlations, wider time windows. If MEDIUM+ patterns found → triggers a proactive Council Round. Messages appear in chat when Shay opens the app next morning.

Detectors: all detectors.

### 3. Weekly Review Scan (Sunday 8:00 PM Perth time)
Deepest analysis — 7-day and 30-day windows, averages, trends, highs and lows. Feeds into Aurore's Weekly Council Review.

Detectors: all detectors + weekly summary statistics.

---

## Severity Levels

| Severity | Action | Example |
|---|---|---|
| **LOW** | Stored as AgentInsight. Referenced in weekly review or future rounds. No proactive round. | "Mood averaged 7.2 this week, up from 6.4" |
| **MEDIUM** | Triggers proactive round. Brief single-agent response. | "Anxiety has been climbing since Tuesday" |
| **HIGH** | Full proactive round, multi-agent response. | Burnout risk detected — sustained high anxiety + low recovery + low mood |

---

## AgentInsight Model

Distinct from `CouncilMessage`. Insights are persistent observations — state, not conversation. They appear as cards on the dashboard and agents reference them in future rounds.

| Field | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `pattern_type` | Enum | See pattern categories above |
| `severity` | Enum | `low`, `medium`, `high` |
| `owning_agent` | String | Which agent owns/speaks about this insight |
| `title` | String(200) | Dashboard card title, e.g. "Anxiety trending up" |
| `detail` | Text | Longer description with data points |
| `supporting_data` | JSON | Raw data backing the insight, e.g. `{"metric": "anxiety", "values": [4,5,5,6,7]}` |
| `status` | Enum | `active`, `acknowledged`, `resolved`, `expired` |
| `created_at` | DateTime | |
| `last_triggered_at` | DateTime | Updated each time pattern re-detected (keeps it fresh) |
| `resolved_at` | DateTime, nullable | |
| `triggered_round_id` | Integer FK, nullable | Links to the Council Round triggered (if any) |
| `pattern_key` | String(200), unique | Deduplication key, e.g. `"trend:anxiety:up:2026-03-10:2026-03-15"` |

### Lifecycle
- **Active** → currently relevant, shown on dashboard
- **Acknowledged** → user tapped "got it" or agent referenced it
- **Resolved** → pattern no longer present in data
- **Expired** → older than 14 days without re-triggering

---

## Detector Architecture

Each detector is a class inheriting from `PatternDetectorBase`:
- Takes a DB session and target date
- Queries relevant data
- Returns a list of `PatternCandidate` objects (or empty list)
- Stateless and idempotent — reports what it sees, doesn't decide whether to act

### Implemented Detectors

**Trend detectors:** `AnxietyTrendDetector`, `MoodTrendDetector`, `EnergyTrendDetector`, `RecoveryTrendDetector`

**Threshold detectors:** `RecoveryThresholdDetector` (< 30%), `AnxietyThresholdDetector` (≥ 9)

**Absence detectors:** `MissedCheckInDetector`, `MissedWorkoutDetector`, `SkincareScheduleDetector`

**Streak detectors:** `StreakAtRiskDetector`, `StreakMilestoneDetector`

**Cross-domain detectors:** `SleepAnxietyCorrelationDetector`, `StressRecoveryCorrelationDetector`, `BurnoutRiskDetector`

### Adding New Detectors
1. Create a class inheriting from `PatternDetectorBase`
2. Implement `detect(as_of_date)` → returns `List[PatternCandidate]`
3. Register in `ALL_DETECTORS` and the appropriate trigger list
4. The runner handles execution, deduplication, and round triggering automatically

---

## Deduplication

The `pattern_key` prevents the same pattern from being flagged repeatedly:
- If an active AgentInsight exists with the same key and was triggered within the last 3 days → update `last_triggered_at` but don't create a new round
- If the pattern escalates (e.g. anxiety moves from 7 to 9) → new key, new detection

---

## Integration with Check-in Flow

```
User confirms check-in
    → Save to DB
    → DetectionRunner.run_post_checkin()
    → Candidates injected into RoundContext.detected_patterns
    → CouncilRoundService.execute_round() fires with enriched context
    → Agents see both check-in data AND pattern detections
```

This means if Shay submits anxiety: 7, and the detector sees it's the 5th consecutive day of increase, Sage's prompt includes both facts. She responds to the trend, not just today's number.

---

## Dashboard Surfacing

Active insights appear as persistent cards below the greeting:

```
GET /insights/active  → Returns up to 5 active AgentInsights, ordered by severity
POST /insights/{id}/acknowledge  → User tapped "Got it"
```

Cards show: owning agent avatar, title, brief detail. Tappable → opens Council Chat at relevant round. Dismissible → sets status to acknowledged.

Colour-coded: blush border for MEDIUM, gold for positive patterns, warm red-brown for HIGH.

---

## Scheduler Setup (Phase 1: APScheduler, Phase 2: Railway cron / Celery)

```python
# Nightly scan: 10:30 PM Perth time (UTC+8)
scheduler.add_job(nightly_detection_scan, CronTrigger(hour=22, minute=30, timezone="Australia/Perth"))

# Weekly review: Sunday 8:00 PM Perth time
scheduler.add_job(weekly_review_scan, CronTrigger(day_of_week="sun", hour=20, minute=0, timezone="Australia/Perth"))
```

Registered in `main.py` on FastAPI startup.
