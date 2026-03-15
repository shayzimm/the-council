"""
Aura — Proactive Pattern Detection Architecture
==================================================

Design sketch for the pattern detection system that lets the Council
notice things before Shay does and speak up unprompted.

Two layers:
  1. Rule-based pattern engine → generates candidate patterns
  2. Aurore (Claude) interpretation → filters candidates, assigns severity,
     decides which agents respond

Three triggers:
  - Post-check-in scan (synchronous, lightweight)
  - Nightly scheduled scan (catches absences, cross-domain correlations)
  - Weekly review scan (feeds Aurore's Weekly Council Review)

Depends on:
  - council_round_architecture.py (CouncilRoundService, RoundTrigger)
  - checkin_architecture.py (CheckInAM, CheckInPM models)

Covers:
  1. AgentInsight model (persistent observations, distinct from chat messages)
  2. Pattern detector rules
  3. Detection runner (orchestrates rules, assembles candidates)
  4. Aurore interpretation layer
  5. Proactive round triggering
  6. Scheduler integration
  7. Dashboard surfacing
"""

# =============================================================================
# 1. DATA MODELS
# =============================================================================

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

# from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Date, JSON, Enum as SAEnum
# from database import Base


class PatternType(str, Enum):
    TREND_UP = "trend_up"           # Metric rising consistently
    TREND_DOWN = "trend_down"       # Metric falling consistently
    THRESHOLD_BREACH = "threshold"  # Single value crosses a critical boundary
    ABSENCE = "absence"             # Expected data is missing
    CORRELATION = "correlation"     # Cross-domain pattern
    STREAK_AT_RISK = "streak_risk"  # A habit streak is about to break
    STREAK_MILESTONE = "streak_milestone"  # Hit a notable streak count
    POSITIVE_TREND = "positive"     # Something is going well


class Severity(str, Enum):
    LOW = "low"         # Store insight, reference later. No proactive round.
    MEDIUM = "medium"   # Trigger proactive round, brief single-agent response.
    HIGH = "high"       # Full proactive round, multi-agent response.


class InsightStatus(str, Enum):
    ACTIVE = "active"       # Currently relevant, shown on dashboard
    ACKNOWLEDGED = "acknowledged"  # User tapped "got it" or agent referenced it
    RESOLVED = "resolved"   # Pattern no longer present
    EXPIRED = "expired"     # Aged out (>14 days without re-triggering)


class AgentInsight:
    """
    A persistent observation about a detected pattern.

    Unlike CouncilMessages (which are conversational and chronological),
    insights are STATE — they represent something the Council currently
    knows about Shay's data. They appear as cards on the dashboard
    and can be referenced by agents in future rounds.

    Examples:
      - "Anxiety has been trending up for 5 days (4→5→5→6→7)"
      - "Training streak: 14 days — longest yet!"
      - "PM check-ins missed 3 of last 5 days"
      - "Mood drops consistently on days after poor sleep (<60%)"
    """
    __tablename__ = "agent_insights"

    # id = Column(Integer, primary_key=True)

    # What pattern was detected
    # pattern_type = Column(SAEnum(PatternType), nullable=False)
    # severity = Column(SAEnum(Severity), nullable=False)

    # Which agent owns this insight (who should speak about it)
    # owning_agent = Column(String(50), nullable=False)
    # ^ "sage" for anxiety trends, "rex" for training streaks, etc.

    # Human-readable summary (shown on dashboard)
    # title = Column(String(200), nullable=False)
    # ^ e.g. "Anxiety trending up"

    # detail = Column(Text, nullable=False)
    # ^ e.g. "Your anxiety scores have risen from 4 to 7 over the last 5 days."

    # The raw data that supports this insight
    # supporting_data = Column(JSON, nullable=True)
    # ^ e.g. {"metric": "anxiety", "values": [4, 5, 5, 6, 7], "dates": [...]}

    # Lifecycle
    # status = Column(SAEnum(InsightStatus), default=InsightStatus.ACTIVE)
    # created_at = Column(DateTime, default=datetime.utcnow)
    # last_triggered_at = Column(DateTime, default=datetime.utcnow)
    # ^ Updated each time the pattern is re-detected (keeps it fresh)
    # resolved_at = Column(DateTime, nullable=True)

    # Link to the Council Round that was triggered (if any)
    # triggered_round_id = Column(Integer, ForeignKey("council_rounds.id"), nullable=True)

    # Deduplication key — prevents the same pattern from being flagged repeatedly
    # pattern_key = Column(String(200), unique=True, nullable=False)
    # ^ e.g. "trend:anxiety:up:2026-03-10:2026-03-15"
    pass


# =============================================================================
# 2. PATTERN CANDIDATE (internal, not persisted)
# =============================================================================

class PatternCandidate(BaseModel):
    """
    Output of a pattern detector rule.
    Not persisted directly — Aurore reviews these and decides
    which become AgentInsights and/or trigger proactive rounds.
    """
    pattern_type: PatternType
    severity: Severity
    owning_agent: str
    title: str
    detail: str
    supporting_data: Dict[str, Any] = {}
    pattern_key: str  # Deduplication key

    # Used by Aurore to decide whether to act
    days_active: int = 1  # How many days this pattern has been present
    is_new: bool = True    # First time detected vs re-detection


# =============================================================================
# 3. PATTERN DETECTOR RULES
# =============================================================================

"""
Each rule is a function that:
  - Takes a DB session and a date range
  - Queries relevant data
  - Returns a list of PatternCandidates (possibly empty)

Rules are stateless and idempotent — they look at the data and report
what they see. They don't decide whether to act; that's Aurore's job.
"""


class PatternDetectorBase:
    """Base class for all pattern detector rules."""

    def __init__(self, db_session):
        self.db = db_session

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        """Override in subclasses. Return detected patterns."""
        raise NotImplementedError


# --- TREND DETECTORS ---

class AnxietyTrendDetector(PatternDetectorBase):
    """
    Detects sustained directional movement in anxiety scores.
    Looks at the last 5-7 AM check-ins.
    """

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []

        # Fetch last 7 AM check-ins
        # checkins = (
        #     self.db.query(CheckInAM)
        #     .filter(CheckInAM.date <= as_of_date)
        #     .order_by(CheckInAM.date.desc())
        #     .limit(7)
        #     .all()
        # )

        # Placeholder data for sketch:
        checkins = [
            {"date": "2026-03-15", "anxiety": 7},
            {"date": "2026-03-14", "anxiety": 6},
            {"date": "2026-03-13", "anxiety": 5},
            {"date": "2026-03-12", "anxiety": 5},
            {"date": "2026-03-11", "anxiety": 4},
        ]

        if len(checkins) < 3:
            return candidates

        values = [c["anxiety"] for c in checkins]
        values.reverse()  # Chronological order

        # Check for consistent upward trend (3+ consecutive increases or stable-then-increase)
        if self._is_trending_up(values, min_points=3, min_delta=2):
            severity = Severity.HIGH if values[-1] >= 7 else Severity.MEDIUM
            candidates.append(PatternCandidate(
                pattern_type=PatternType.TREND_UP,
                severity=severity,
                owning_agent="sage",
                title="Anxiety trending up",
                detail=(
                    f"Your anxiety scores have moved from {values[0]} to {values[-1]} "
                    f"over the last {len(values)} check-ins."
                ),
                supporting_data={
                    "metric": "anxiety",
                    "values": values,
                    "dates": [c["date"] for c in checkins],
                },
                pattern_key=f"trend:anxiety:up:{checkins[0]['date']}:{checkins[-1]['date']}",
                days_active=len(values),
            ))

        return candidates

    def _is_trending_up(self, values: list, min_points: int = 3, min_delta: int = 2) -> bool:
        """
        Returns True if values show a consistent upward trend.
        Allows for one plateau (equal consecutive values) but not decreases.
        """
        if len(values) < min_points:
            return False
        if values[-1] - values[0] < min_delta:
            return False

        decreases = sum(1 for i in range(1, len(values)) if values[i] < values[i - 1])
        return decreases == 0  # No decreases allowed


class MoodTrendDetector(PatternDetectorBase):
    """Same structure as anxiety but for mood (inverted — downward is concerning)."""

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []
        # Similar to AnxietyTrendDetector but:
        # - Looks for DOWNWARD trend in mood
        # - Severity: HIGH if mood drops below 4, MEDIUM otherwise
        # - owning_agent: "sage"
        # - Cross-references with anxiety (if both trending bad → escalate severity)
        return candidates


class EnergyTrendDetector(PatternDetectorBase):
    """Detects sustained low energy — might indicate overtraining, poor sleep, or burnout."""

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []
        # Looks for: energy consistently below 5 for 4+ days
        # owning_agent: depends on context
        #   - If recovery also low → "rex" (overtraining signal)
        #   - If mood also low → "sage" (burnout signal)
        #   - Default: "aurore" (cross-domain)
        return candidates


class RecoveryTrendDetector(PatternDetectorBase):
    """Detects declining Whoop recovery scores."""

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []
        # Fetch last 7 WhoopSnapshots
        # Trend detection: recovery declining over 5+ days
        # Threshold: recovery below 33% → HIGH severity
        # owning_agent: "rex"
        return candidates


# --- THRESHOLD DETECTORS ---

class RecoveryThresholdDetector(PatternDetectorBase):
    """Single-day recovery breach — below 30% is a red flag."""

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []
        # whoop = self.db.query(WhoopSnapshot).filter_by(date=as_of_date).first()
        # if whoop and whoop.recovery_score < 30:
        #     candidates.append(PatternCandidate(
        #         pattern_type=PatternType.THRESHOLD_BREACH,
        #         severity=Severity.HIGH,
        #         owning_agent="rex",
        #         title="Recovery critically low",
        #         detail=f"Recovery at {whoop.recovery_score}%. Rest day strongly recommended.",
        #         supporting_data={"recovery": whoop.recovery_score, "hrv": whoop.hrv},
        #         pattern_key=f"threshold:recovery:low:{as_of_date}",
        #     ))
        return candidates


class AnxietyThresholdDetector(PatternDetectorBase):
    """Anxiety at 9 or 10 — immediate Sage response warranted."""

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []
        # today_am = self.db.query(CheckInAM).filter_by(date=as_of_date).first()
        # if today_am and today_am.anxiety >= 9:
        #     candidates.append(PatternCandidate(
        #         pattern_type=PatternType.THRESHOLD_BREACH,
        #         severity=Severity.HIGH,
        #         owning_agent="sage",
        #         title="Anxiety very high",
        #         detail=f"Anxiety at {today_am.anxiety}/10 today. Sage should respond with immediate support.",
        #         pattern_key=f"threshold:anxiety:high:{as_of_date}",
        #     ))
        return candidates


# --- ABSENCE DETECTORS ---

class MissedCheckInDetector(PatternDetectorBase):
    """
    Detects missing check-ins. Runs in the nightly scan.
    """

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []

        # Count missed AM check-ins in last 5 days
        # last_5_days = [as_of_date - timedelta(days=i) for i in range(5)]
        # existing_am = self.db.query(CheckInAM.date).filter(CheckInAM.date.in_(last_5_days)).all()
        # existing_dates = {row.date for row in existing_am}
        # missed = [d for d in last_5_days if d not in existing_dates]

        missed = []  # Placeholder

        if len(missed) >= 3:
            candidates.append(PatternCandidate(
                pattern_type=PatternType.ABSENCE,
                severity=Severity.MEDIUM,
                owning_agent="sage",
                title="Check-ins dropping off",
                detail=(
                    f"You've missed {len(missed)} of the last 5 morning check-ins. "
                    "No pressure — but the Council works better with consistent data."
                ),
                supporting_data={"missed_dates": [str(d) for d in missed]},
                pattern_key=f"absence:checkin_am:{as_of_date}",
                days_active=len(missed),
            ))

        return candidates


class MissedWorkoutDetector(PatternDetectorBase):
    """
    Detects workout frequency dropping below expected cadence.
    Shay's target: 4 sessions per week (upper/lower split + Saturday).
    """

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []
        # Count workouts in last 7 days
        # If < 3 (below 4-day target with 1-day grace): flag
        # owning_agent: "rex"
        # severity: MEDIUM (first week), HIGH (second consecutive week)
        return candidates


class SkincareScheduleDetector(PatternDetectorBase):
    """
    Detects missed tret nights or skincare routine gaps.
    Celeste owns the tret/azelaic schedule.
    """

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []
        # Check SkinRoutine logs against expected tret schedule
        # If tret night was scheduled but not logged → flag
        # If PM skincare missed 2+ nights this week → flag
        # owning_agent: "celeste"
        return candidates


# --- STREAK DETECTORS ---

class StreakAtRiskDetector(PatternDetectorBase):
    """
    Detects when a habit streak is at risk of breaking.
    If last_completed was yesterday and today's data isn't logged yet
    (and it's getting late), the streak is at risk.
    """

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []
        # streaks = self.db.query(HabitStreak).filter(
        #     HabitStreak.current_streak >= 5,  # Only flag for meaningful streaks
        #     HabitStreak.last_completed == as_of_date - timedelta(days=1),
        # ).all()
        #
        # for streak in streaks:
        #     candidates.append(PatternCandidate(
        #         pattern_type=PatternType.STREAK_AT_RISK,
        #         severity=Severity.LOW,  # Gentle nudge, not alarm
        #         owning_agent=self._streak_agent(streak.habit_name),
        #         title=f"{streak.habit_name} streak at risk",
        #         detail=f"Your {streak.current_streak}-day {streak.habit_name} streak is at risk.",
        #         pattern_key=f"streak_risk:{streak.habit_name}:{as_of_date}",
        #     ))
        return candidates

    def _streak_agent(self, habit_name: str) -> str:
        mapping = {
            "Training": "rex",
            "Skincare": "celeste",
            "Check-ins": "sage",
            "NSDR": "sage",
        }
        return mapping.get(habit_name, "aurore")


class StreakMilestoneDetector(PatternDetectorBase):
    """
    Detects notable streak milestones: 7, 14, 21, 30, 60, 90 days.
    These are POSITIVE patterns — agents should celebrate.
    """

    MILESTONES = [7, 14, 21, 30, 60, 90]

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []
        # streaks = self.db.query(HabitStreak).filter(
        #     HabitStreak.current_streak.in_(self.MILESTONES),
        #     HabitStreak.last_completed == as_of_date,
        # ).all()
        #
        # for streak in streaks:
        #     candidates.append(PatternCandidate(
        #         pattern_type=PatternType.STREAK_MILESTONE,
        #         severity=Severity.LOW,  # Celebration, not urgency
        #         owning_agent=self._streak_agent(streak.habit_name),
        #         title=f"{streak.habit_name}: {streak.current_streak} days!",
        #         detail=f"{streak.current_streak}-day {streak.habit_name} streak. Worth celebrating.",
        #         pattern_key=f"streak_milestone:{streak.habit_name}:{streak.current_streak}",
        #     ))
        return candidates


# --- CROSS-DOMAIN CORRELATION DETECTORS ---

class SleepAnxietyCorrelationDetector(PatternDetectorBase):
    """
    Detects if poor sleep (Whoop <60%) consistently precedes high anxiety.
    Requires 14+ days of data to be meaningful.
    """

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []
        # Fetch last 14 days of Whoop sleep + next-day AM anxiety
        # Calculate: on days where sleep_performance < 60%, what's the avg anxiety?
        # Compare to days where sleep_performance >= 60%
        # If difference > 2 points on the anxiety scale → flag correlation

        # owning_agent: "aurore" (cross-domain) or "sage" (if actionable)
        # This is a slow-burn insight — always LOW severity
        # Surfaces in the weekly review, not as an interruption
        return candidates


class StressRecoveryCorrelationDetector(PatternDetectorBase):
    """
    Detects if sustained high anxiety correlates with declining recovery.
    The cortisol-recovery connection.
    """

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []
        # If anxiety avg > 6 for 5+ days AND recovery is trending down → flag
        # owning_agent: "aurore" (Sage + Rex both need to see this)
        # severity: MEDIUM (both agents should respond)
        return candidates


class BurnoutRiskDetector(PatternDetectorBase):
    """
    Composite detector: high stress + low recovery + low mood + low energy
    sustained over 5+ days = burnout risk flag.

    This is a HIGH severity pattern that triggers a full Council response.
    """

    async def detect(self, as_of_date: date) -> List[PatternCandidate]:
        candidates = []

        # Fetch last 5 days of AM check-ins + Whoop
        # Burnout signal if ALL of these are true:
        #   - avg anxiety > 6
        #   - avg mood < 5
        #   - avg energy < 5
        #   - avg recovery < 50%
        #   - duration: 5+ consecutive days

        # This is the most serious proactive detection.
        # owning_agent: "sage" (primary), but Aurore should flag to all agents.
        # severity: HIGH

        # Example candidate:
        # candidates.append(PatternCandidate(
        #     pattern_type=PatternType.CORRELATION,
        #     severity=Severity.HIGH,
        #     owning_agent="sage",
        #     title="Burnout risk detected",
        #     detail=(
        #         "Over the last 5 days: anxiety averaging 7.2, mood 4.4, energy 3.8, "
        #         "recovery 41%. This combination is a strong burnout signal. "
        #         "The Council should respond with a coordinated plan."
        #     ),
        #     supporting_data={...},
        #     pattern_key=f"composite:burnout_risk:{as_of_date}",
        # ))

        return candidates


# =============================================================================
# 4. DETECTION RUNNER
# =============================================================================

"""
The detection runner orchestrates all pattern detectors,
deduplicates candidates, and passes them to Aurore for interpretation.
"""

# Registry of all active detectors
ALL_DETECTORS = [
    # Trends
    AnxietyTrendDetector,
    MoodTrendDetector,
    EnergyTrendDetector,
    RecoveryTrendDetector,

    # Thresholds
    RecoveryThresholdDetector,
    AnxietyThresholdDetector,

    # Absences
    MissedCheckInDetector,
    MissedWorkoutDetector,
    SkincareScheduleDetector,

    # Streaks
    StreakAtRiskDetector,
    StreakMilestoneDetector,

    # Cross-domain
    SleepAnxietyCorrelationDetector,
    StressRecoveryCorrelationDetector,
    BurnoutRiskDetector,
]

# Which detectors run in which context:
POST_CHECKIN_DETECTORS = [
    AnxietyTrendDetector,
    MoodTrendDetector,
    EnergyTrendDetector,
    RecoveryThresholdDetector,
    AnxietyThresholdDetector,
    StreakMilestoneDetector,
]

NIGHTLY_DETECTORS = ALL_DETECTORS  # Run everything

WEEKLY_DETECTORS = ALL_DETECTORS   # Run everything + wider time windows


class DetectionRunner:
    """
    Runs pattern detectors, deduplicates results, and decides
    whether to trigger a proactive Council Round.
    """

    def __init__(self, db_session):
        self.db = db_session

    async def run_post_checkin(self, as_of_date: date) -> List[PatternCandidate]:
        """
        Lightweight scan after a check-in is submitted.
        Returns candidates to inject into the check-in's Council Round context.
        Does NOT trigger a separate proactive round — the check-in round handles it.
        """
        return await self._run_detectors(POST_CHECKIN_DETECTORS, as_of_date)

    async def run_nightly(self, as_of_date: date) -> List[PatternCandidate]:
        """
        Full scan run by the scheduler each night.
        May trigger a proactive Council Round if MEDIUM+ patterns are found.
        """
        candidates = await self._run_detectors(NIGHTLY_DETECTORS, as_of_date)
        candidates = self._deduplicate(candidates, as_of_date)

        # Separate by severity
        actionable = [c for c in candidates if c.severity in (Severity.MEDIUM, Severity.HIGH)]
        low_severity = [c for c in candidates if c.severity == Severity.LOW]

        # Store low-severity as insights (no proactive round)
        for candidate in low_severity:
            await self._upsert_insight(candidate)

        # If there are actionable patterns, send them to Aurore for interpretation
        if actionable:
            await self._trigger_proactive_round(actionable, as_of_date)

        return candidates

    async def run_weekly(self, as_of_date: date) -> Dict[str, Any]:
        """
        Deep scan for the Weekly Council Review.
        Returns a comprehensive summary for Aurore to synthesise.
        """
        candidates = await self._run_detectors(WEEKLY_DETECTORS, as_of_date)

        # Also compute summary statistics
        summary = await self._compute_weekly_summary(as_of_date)

        return {
            "patterns": [c.model_dump() for c in candidates],
            "summary": summary,
        }

    async def _run_detectors(
        self,
        detector_classes: list,
        as_of_date: date,
    ) -> List[PatternCandidate]:
        """Run a list of detector classes and collect all candidates."""
        all_candidates = []
        for detector_cls in detector_classes:
            detector = detector_cls(self.db)
            try:
                candidates = await detector.detect(as_of_date)
                all_candidates.extend(candidates)
            except Exception as e:
                # Log error but don't fail the whole scan
                print(f"Detector {detector_cls.__name__} failed: {e}")
        return all_candidates

    def _deduplicate(
        self,
        candidates: List[PatternCandidate],
        as_of_date: date,
    ) -> List[PatternCandidate]:
        """
        Remove candidates that match an already-active AgentInsight.
        A pattern is considered duplicate if:
          - Same pattern_key exists in agent_insights
          - That insight was triggered within the last 3 days
          - That insight hasn't been resolved
        """
        deduplicated = []
        for candidate in candidates:
            # existing = self.db.query(AgentInsight).filter(
            #     AgentInsight.pattern_key == candidate.pattern_key,
            #     AgentInsight.status == InsightStatus.ACTIVE,
            #     AgentInsight.last_triggered_at >= as_of_date - timedelta(days=3),
            # ).first()
            #
            # if existing:
            #     # Update last_triggered_at to keep it fresh
            #     existing.last_triggered_at = datetime.utcnow()
            #     candidate.is_new = False
            # else:
            #     candidate.is_new = True

            deduplicated.append(candidate)

        return deduplicated

    async def _upsert_insight(self, candidate: PatternCandidate):
        """
        Create or update an AgentInsight from a pattern candidate.
        """
        # existing = self.db.query(AgentInsight).filter_by(
        #     pattern_key=candidate.pattern_key,
        # ).first()
        #
        # if existing:
        #     existing.last_triggered_at = datetime.utcnow()
        #     existing.detail = candidate.detail
        #     existing.supporting_data = candidate.supporting_data
        #     existing.status = InsightStatus.ACTIVE
        # else:
        #     insight = AgentInsight(
        #         pattern_type=candidate.pattern_type,
        #         severity=candidate.severity,
        #         owning_agent=candidate.owning_agent,
        #         title=candidate.title,
        #         detail=candidate.detail,
        #         supporting_data=candidate.supporting_data,
        #         pattern_key=candidate.pattern_key,
        #     )
        #     self.db.add(insight)
        pass

    async def _trigger_proactive_round(
        self,
        candidates: List[PatternCandidate],
        as_of_date: date,
    ):
        """
        Send actionable patterns to a proactive Council Round.

        The patterns are injected into the round's trigger_data so
        Aurore can reference them in her triage and the agents can
        see what was detected.
        """
        # from council_round_architecture import CouncilRoundService, RoundTrigger
        #
        # trigger_data = {
        #     "detected_patterns": [c.model_dump() for c in candidates],
        #     "detection_date": as_of_date.isoformat(),
        #     "most_severe": max(candidates, key=lambda c: c.severity.value).title,
        # }
        #
        # service = CouncilRoundService(self.db)
        # result = await service.execute_round(
        #     trigger_type=RoundTrigger.PROACTIVE,
        #     trigger_data=trigger_data,
        # )
        #
        # # Link insights to the triggered round
        # for candidate in candidates:
        #     await self._upsert_insight(candidate)
        #     insight = self.db.query(AgentInsight).filter_by(
        #         pattern_key=candidate.pattern_key,
        #     ).first()
        #     if insight:
        #         insight.triggered_round_id = result["round_id"]
        #
        # self.db.commit()
        pass

    async def _compute_weekly_summary(self, as_of_date: date) -> dict:
        """
        Compute aggregate statistics for the weekly review.
        Fed into Aurore's Weekly Council Review prompt.
        """
        week_start = as_of_date - timedelta(days=6)

        # Placeholder structure:
        return {
            "period": f"{week_start.isoformat()} to {as_of_date.isoformat()}",
            "checkin_completion": {
                "am_completed": 5,
                "am_total": 7,
                "pm_completed": 4,
                "pm_total": 7,
            },
            "averages": {
                "energy": 5.4,
                "mood": 6.2,
                "anxiety": 5.8,
                "day_rating": 6.5,
                "recovery": 58.3,
                "hrv": 45.2,
                "sleep_performance": 72.1,
            },
            "workouts": {
                "completed": 4,
                "target": 5,
            },
            "skincare": {
                "am_adherence": "6/7",
                "pm_adherence": "5/7",
                "tret_nights": 1,
                "tret_target": 1,  # Every 6 days
            },
            "streaks": {
                "Training": 14,
                "Skincare": 8,
                "Check-ins": 5,
            },
            "highlights": [
                "Longest training streak yet (14 days)",
                "Mood averaged above 6 for the second consecutive week",
            ],
            "concerns": [
                "Anxiety trending up since Wednesday",
                "PM check-ins missed twice this week",
            ],
        }


# =============================================================================
# 5. INTEGRATION WITH CHECK-IN FLOW
# =============================================================================

"""
The post-check-in detection runs BEFORE the Council Round is triggered.
Detected patterns are injected into the round context so agents can
reference them naturally.

Modified flow from checkin_architecture.py:

  1. User confirms check-in → saved to DB
  2. DetectionRunner.run_post_checkin() → returns PatternCandidates
  3. Candidates injected into RoundContext.detected_patterns
  4. CouncilRoundService.execute_round() fires with enriched context
  5. Agents see both the check-in data AND the pattern detections

This means if Shay submits a morning check-in with anxiety: 7,
and the trend detector sees it's the 5th consecutive day of rising anxiety,
Sage's prompt includes both facts. Sage doesn't just respond to today's 7 —
she responds to the five-day trend.
"""

# Example modification to the RoundContext model:
class EnrichedRoundContext(BaseModel):
    """Extended RoundContext with pattern detection data."""

    # ... all existing RoundContext fields ...

    detected_patterns: List[Dict[str, Any]] = []
    # ^ Pattern candidates from the post-check-in scan.
    # Each dict is a PatternCandidate.model_dump()

    active_insights: List[Dict[str, Any]] = []
    # ^ Currently active AgentInsights from the DB.
    # Agents can reference these for continuity:
    # "As I mentioned on Tuesday, your anxiety has been climbing..."


# =============================================================================
# 6. SCHEDULER INTEGRATION
# =============================================================================

"""
The nightly and weekly scans need to run on a schedule.

For Phase 1 (local dev), use APScheduler with FastAPI:

    pip install apscheduler

For Phase 2 (production), migrate to:
  - Railway cron jobs, or
  - Celery + Redis, or
  - Simple cron calling an internal API endpoint

The scheduler is registered in main.py on app startup.
"""

# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from apscheduler.triggers.cron import CronTrigger


def setup_scheduler(app):
    """
    Register scheduled jobs on FastAPI startup.
    Called from main.py:

        @app.on_event("startup")
        async def startup():
            setup_scheduler(app)
    """
    # scheduler = AsyncIOScheduler()
    #
    # # Nightly scan: 10:30 PM Perth time (UTC+8)
    # scheduler.add_job(
    #     nightly_detection_scan,
    #     CronTrigger(hour=22, minute=30, timezone="Australia/Perth"),
    #     id="nightly_detection",
    #     name="Nightly pattern detection scan",
    # )
    #
    # # Weekly review: Sunday 8:00 PM Perth time
    # scheduler.add_job(
    #     weekly_review_scan,
    #     CronTrigger(day_of_week="sun", hour=20, minute=0, timezone="Australia/Perth"),
    #     id="weekly_review",
    #     name="Weekly Council Review generation",
    # )
    #
    # scheduler.start()
    # app.state.scheduler = scheduler
    pass


async def nightly_detection_scan():
    """Run the nightly pattern detection scan."""
    # db = SessionLocal()
    # try:
    #     runner = DetectionRunner(db)
    #     await runner.run_nightly(date.today())
    # finally:
    #     db.close()
    pass


async def weekly_review_scan():
    """
    Run the weekly review scan and trigger Aurore's Weekly Council Review.
    """
    # db = SessionLocal()
    # try:
    #     runner = DetectionRunner(db)
    #     weekly_data = await runner.run_weekly(date.today())
    #
    #     # Trigger a WEEKLY_REVIEW Council Round with the summary data
    #     service = CouncilRoundService(db)
    #     await service.execute_round(
    #         trigger_type=RoundTrigger.WEEKLY_REVIEW,
    #         trigger_data=weekly_data,
    #     )
    # finally:
    #     db.close()
    pass


# =============================================================================
# 7. DASHBOARD SURFACING
# =============================================================================

"""
Active insights appear on the dashboard as persistent cards.
They're distinct from chat messages — they don't scroll away.

API endpoint:

  GET /insights/active
  → Returns currently active AgentInsights for dashboard display

Dashboard component: InsightCards
  - Renders a row of insight cards below the greeting
  - Each card has: owning agent avatar, title, brief detail
  - Tappable → opens the Council Chat at the relevant round
  - Dismissible → sets status to ACKNOWLEDGED (but still available in history)
  - Colour-coded by severity: blush border for MEDIUM, gold for positive, 
    a warm red-brown for HIGH

Example dashboard rendering:

  ┌──────────────────────────────────────────────────┐
  │ 🌿 Sage                                         │
  │ Anxiety trending up                              │
  │ Scores have risen from 4 to 7 over 5 days.      │
  │                                          [Got it]│
  └──────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────┐
  │ 💪 Rex                                           │
  │ Training streak: 14 days!                        │
  │ Your longest streak yet. Keep building.          │
  └──────────────────────────────────────────────────┘


These cards are the visible face of the proactive system.
They make the Council feel like it's watching and thinking
even when Shay isn't actively chatting or checking in.
"""


# --- API Route ---
# @router.get("/insights/active")
async def get_active_insights():
    """Return currently active insights for dashboard display."""
    # db = get_db()
    # insights = (
    #     db.query(AgentInsight)
    #     .filter(AgentInsight.status == InsightStatus.ACTIVE)
    #     .order_by(AgentInsight.severity.desc(), AgentInsight.last_triggered_at.desc())
    #     .limit(5)  # Max 5 cards on dashboard
    #     .all()
    # )
    # return [insight.to_dict() for insight in insights]
    pass


# --- Insight lifecycle ---
# @router.post("/insights/{insight_id}/acknowledge")
async def acknowledge_insight(insight_id: int):
    """User tapped 'Got it' — mark as acknowledged."""
    # insight = db.query(AgentInsight).get(insight_id)
    # insight.status = InsightStatus.ACKNOWLEDGED
    # db.commit()
    pass


# --- Expiration (runs as part of nightly scan) ---
async def expire_stale_insights(db_session, as_of_date: date):
    """
    Insights older than 14 days without re-triggering are expired.
    This prevents the dashboard from accumulating stale cards.
    """
    # cutoff = as_of_date - timedelta(days=14)
    # stale = db_session.query(AgentInsight).filter(
    #     AgentInsight.status == InsightStatus.ACTIVE,
    #     AgentInsight.last_triggered_at < cutoff,
    # ).all()
    # for insight in stale:
    #     insight.status = InsightStatus.EXPIRED
    pass


# =============================================================================
# 8. ADDING NEW DETECTORS
# =============================================================================

"""
To add a new pattern detector:

1. Create a class inheriting from PatternDetectorBase
2. Implement the detect() method:
   - Query relevant data from the DB
   - Apply your detection logic
   - Return a list of PatternCandidates (or empty list)
3. Add the class to ALL_DETECTORS
4. Add to the appropriate trigger list (POST_CHECKIN_DETECTORS, etc.)

The runner handles execution, deduplication, and round triggering
automatically. You just define what to look for.

As the app grows, new detectors can be added for:
- Nutrition patterns (Nadia, Phase 2)
- Cycle-related correlations (Dr. Vera, Phase 3)
- Hair/skin photo comparison triggers (Celeste/Ines, Phase 2+)
- Style consistency patterns (Margot, Phase 3)
"""
