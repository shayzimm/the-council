"""
Aura — Check-in System Architecture
=====================================

Design sketch for the low-friction check-in system.
Two modes: Conversational (default) and Quick-tap (fallback).
Both produce the same structured data and trigger a Council Round.

Depends on: council_round_architecture.py (CouncilRoundService)

Covers:
  1. Data models for check-ins
  2. Conversational extraction (Claude API)
  3. Quick-tap schema
  4. API routes
  5. Post-check-in → Council Round integration
  6. Backfill support
  7. Frontend component structure
"""

# =============================================================================
# 1. DATA MODELS
# =============================================================================

from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field

# from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Date
# from database import Base


class CheckInMode(str, Enum):
    CONVERSATIONAL = "conversational"
    QUICK_TAP = "quick_tap"
    BACKFILL = "backfill"


# --- SQLAlchemy Models (inherit from your Base) ---

class CheckInAM:
    """Morning check-in — one per day max."""
    __tablename__ = "checkins_am"

    # id = Column(Integer, primary_key=True)
    # date = Column(Date, unique=True, nullable=False)

    # Subjective scores (1-10)
    # energy = Column(Integer, nullable=False)
    # mood = Column(Integer, nullable=False)
    # anxiety = Column(Integer, nullable=False)

    # Optional context
    # sleep_notes = Column(Text, nullable=True)
    # intention = Column(Text, nullable=True)

    # Raw conversational input (stored for reference and reprocessing)
    # raw_input = Column(Text, nullable=True)

    # Metadata
    # mode = Column(String(20), default="conversational")  # conversational | quick_tap | backfill
    # whoop_recovery = Column(Float, nullable=True)   # Snapshotted at check-in time
    # whoop_hrv = Column(Float, nullable=True)
    # whoop_sleep_score = Column(Float, nullable=True)
    # created_at = Column(DateTime, default=datetime.utcnow)
    pass


class CheckInPM:
    """Evening check-in — one per day max."""
    __tablename__ = "checkins_pm"

    # id = Column(Integer, primary_key=True)
    # date = Column(Date, unique=True, nullable=False)

    # Subjective
    # day_rating = Column(Integer, nullable=False)  # 1-10
    # proud_of = Column(Text, nullable=True)
    # council_flag = Column(Text, nullable=True)

    # Auto-populated, user-correctable
    # skincare_done = Column(Boolean, default=False)
    # tasks_completed = Column(JSON, nullable=True)
    # ^ List of task IDs marked done today — pre-filled from task tracking

    # Raw input
    # raw_input = Column(Text, nullable=True)

    # Metadata
    # mode = Column(String(20), default="conversational")
    # whoop_strain = Column(Float, nullable=True)
    # created_at = Column(DateTime, default=datetime.utcnow)
    pass


# --- Pydantic Schemas (API request/response) ---

class CheckInAMConversationalRequest(BaseModel):
    """User submits free-text; backend extracts structured data."""
    raw_input: str = Field(
        ...,
        description="Natural language check-in, e.g. 'Tired, anxious about work'",
        min_length=1,
        max_length=1000,
    )


class CheckInAMQuickTapRequest(BaseModel):
    """User taps values directly — no extraction needed."""
    energy: int = Field(..., ge=1, le=10)
    mood: int = Field(..., ge=1, le=10)
    anxiety: int = Field(..., ge=1, le=10)
    sleep_notes: Optional[str] = None
    intention: Optional[str] = None


class CheckInAMExtractionResult(BaseModel):
    """
    What the extraction model returns.
    Sent back to the frontend for user confirmation/adjustment.
    """
    energy: int = Field(..., ge=1, le=10)
    mood: int = Field(..., ge=1, le=10)
    anxiety: int = Field(..., ge=1, le=10)
    sleep_notes: Optional[str] = None
    intention: Optional[str] = None
    confidence: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="How confident the extraction is overall. Below 0.7, suggest manual adjustment.",
    )
    missing_fields: List[str] = Field(
        default_factory=list,
        description="Fields not mentioned in the input, e.g. ['intention']",
    )
    follow_up_question: Optional[str] = Field(
        None,
        description="If a key field is missing, Aurore's follow-up question.",
    )


class CheckInPMConversationalRequest(BaseModel):
    raw_input: str = Field(..., min_length=1, max_length=1000)


class CheckInPMQuickTapRequest(BaseModel):
    day_rating: int = Field(..., ge=1, le=10)
    skincare_done: bool = False
    proud_of: Optional[str] = None
    council_flag: Optional[str] = None


class CheckInPMExtractionResult(BaseModel):
    day_rating: int = Field(..., ge=1, le=10)
    skincare_done: Optional[bool] = None
    proud_of: Optional[str] = None
    council_flag: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    missing_fields: List[str] = Field(default_factory=list)
    follow_up_question: Optional[str] = None


class CheckInConfirmRequest(BaseModel):
    """
    After extraction, user confirms (possibly with adjustments).
    This is what actually gets saved.
    """
    checkin_type: str = Field(..., pattern="^(am|pm)$")
    date: date

    # AM fields
    energy: Optional[int] = Field(None, ge=1, le=10)
    mood: Optional[int] = Field(None, ge=1, le=10)
    anxiety: Optional[int] = Field(None, ge=1, le=10)
    sleep_notes: Optional[str] = None
    intention: Optional[str] = None

    # PM fields
    day_rating: Optional[int] = Field(None, ge=1, le=10)
    skincare_done: Optional[bool] = None
    proud_of: Optional[str] = None
    council_flag: Optional[str] = None

    # Metadata
    raw_input: Optional[str] = None
    mode: CheckInMode = CheckInMode.CONVERSATIONAL
    is_backfill: bool = False


class CheckInResponse(BaseModel):
    """Returned after a check-in is saved and the Council Round completes."""
    checkin_id: int
    council_round_id: int
    council_messages: List[dict]
    # ^ The user-facing messages from the Council Round.
    # Each dict: { "agent_name": str, "message": str }


# =============================================================================
# 2. CONVERSATIONAL EXTRACTION
# =============================================================================

"""
This is a lightweight Claude API call — NOT a full Council Round.
Its only job is to parse natural language into structured check-in fields.

It runs fast (small prompt, structured output) and returns values for
the user to confirm before saving.
"""

EXTRACTION_SYSTEM_PROMPT_AM = """You extract structured morning check-in data from natural language.

The user (Shay) will describe how she's feeling this morning. Extract:
- energy (1-10): physical and mental energy level
- mood (1-10): overall emotional state
- anxiety (1-10): current anxiety level (10 = very anxious)
- sleep_notes: any sleep-related context (optional)
- intention: any goal or focus mentioned for the day (optional)

RULES:
- If a value isn't mentioned or implied, set it to null and list the field in missing_fields.
- Use the full 1-10 range. "Tired" ≈ 3-4. "Good" ≈ 6-7. "Great" ≈ 8-9. "Awful" ≈ 1-2.
- If anxiety isn't explicitly mentioned but stress is, map stress to anxiety.
- If she mentions sleep quality, map it to both energy context and sleep_notes.
- Set confidence based on how explicitly the values were stated.
  Direct numbers → 0.95. Clear descriptors → 0.8. Vague/minimal → 0.6.
- If intention is missing and confidence is otherwise high, generate a
  follow_up_question like "What's one thing you want to focus on today?"

RESPOND ONLY WITH JSON. No preamble, no markdown, no backticks.

{
  "energy": <int or null>,
  "mood": <int or null>,
  "anxiety": <int or null>,
  "sleep_notes": <string or null>,
  "intention": <string or null>,
  "confidence": <float>,
  "missing_fields": [<string>],
  "follow_up_question": <string or null>
}
"""

EXTRACTION_SYSTEM_PROMPT_PM = """You extract structured evening check-in data from natural language.

The user (Shay) will describe how her day went. Extract:
- day_rating (1-10): overall day quality
- skincare_done: true/false/null — did she do her skincare routine?
- proud_of: anything she's proud of or happy about (optional)
- council_flag: anything she wants to flag for The Council (optional)

RULES:
- Same scale guidance as morning: "Good day" ≈ 7, "Rough" ≈ 3-4, "Amazing" ≈ 9.
- If skincare isn't mentioned, set to null (the system may auto-fill from routine logs).
- Positive accomplishments → proud_of. Concerns or requests → council_flag.
- Confidence scoring: same rules as morning extraction.

RESPOND ONLY WITH JSON. No preamble, no markdown, no backticks.

{
  "day_rating": <int or null>,
  "skincare_done": <bool or null>,
  "proud_of": <string or null>,
  "council_flag": <string or null>,
  "confidence": <float>,
  "missing_fields": [<string>],
  "follow_up_question": <string or null>
}
"""


import json

# from anthropic import Anthropic


async def extract_checkin_am(raw_input: str) -> CheckInAMExtractionResult:
    """
    Send the user's natural language input to Claude for extraction.
    Returns structured data for confirmation.
    """
    # client = Anthropic()
    # response = client.messages.create(
    #     model="claude-sonnet-4-20250514",
    #     max_tokens=300,
    #     system=EXTRACTION_SYSTEM_PROMPT_AM,
    #     messages=[{"role": "user", "content": raw_input}],
    # )
    # raw_json = response.content[0].text

    # Placeholder:
    raw_json = '{"energy": 5, "mood": 6, "anxiety": 7, "sleep_notes": null, "intention": null, "confidence": 0.75, "missing_fields": ["intention"], "follow_up_question": "What\\'s one thing you want to focus on today?"}'

    parsed = json.loads(raw_json)
    return CheckInAMExtractionResult(**parsed)


async def extract_checkin_pm(raw_input: str) -> CheckInPMExtractionResult:
    """Same pattern for evening extraction."""
    # Same Claude API call with PM system prompt
    raw_json = '{"day_rating": 7, "skincare_done": true, "proud_of": "Finished Python exercises", "council_flag": null, "confidence": 0.85, "missing_fields": [], "follow_up_question": null}'
    parsed = json.loads(raw_json)
    return CheckInPMExtractionResult(**parsed)


# =============================================================================
# 3. PRE-POPULATION FROM WHOOP + TASK DATA
# =============================================================================

"""
Before the check-in UI renders, the frontend fetches pre-populated context.
This avoids asking Shay for data the system already has.
"""


class CheckInPrePopulateAM(BaseModel):
    """Context shown at the top of the morning check-in."""
    whoop_available: bool = False
    sleep_duration_hours: Optional[float] = None
    sleep_performance: Optional[int] = None  # Percentage
    recovery_score: Optional[int] = None
    hrv: Optional[int] = None

    # Previous evening check-in (if completed)
    last_evening_rating: Optional[int] = None
    last_evening_proud_of: Optional[str] = None


class CheckInPrePopulatePM(BaseModel):
    """Context shown at the top of the evening check-in."""
    whoop_available: bool = False
    strain_score: Optional[float] = None

    # Auto-detected from today's data
    workout_logged: bool = False
    workout_type: Optional[str] = None
    skincare_logged: bool = False  # From SkinRoutine model
    skincare_active_used: Optional[str] = None  # "tret" | "azelaic" | "none"

    # Today's tasks with completion status
    tasks: List[dict] = []
    # ^ e.g. [{"label": "Upper body", "agent": "Rex", "completed": True}, ...]

    # This morning's check-in (for continuity)
    morning_energy: Optional[int] = None
    morning_mood: Optional[int] = None
    morning_intention: Optional[str] = None


async def get_prepopulate_am(target_date: date, db_session) -> CheckInPrePopulateAM:
    """
    Fetch Whoop data and previous evening context for the morning check-in.
    """
    # whoop = db_session.query(WhoopSnapshot).filter_by(date=target_date).first()
    # last_pm = db_session.query(CheckInPM).filter_by(date=target_date - timedelta(days=1)).first()

    return CheckInPrePopulateAM(
        whoop_available=True,   # Set based on whether Whoop data exists
        sleep_duration_hours=6.2,
        sleep_performance=61,
        recovery_score=42,
        hrv=38,
        last_evening_rating=7,
        last_evening_proud_of="Finished Python exercises",
    )


async def get_prepopulate_pm(target_date: date, db_session) -> CheckInPrePopulatePM:
    """
    Fetch Whoop strain, today's task completion, skincare log, and morning context.
    """
    return CheckInPrePopulatePM(
        whoop_available=True,
        strain_score=12.4,
        workout_logged=True,
        workout_type="Upper body — moderate",
        skincare_logged=True,
        skincare_active_used="azelaic",
        tasks=[
            {"label": "Upper body — moderate intensity", "agent": "Rex", "completed": True},
            {"label": "Azelaic night", "agent": "Celeste", "completed": True},
            {"label": "10 min NSDR", "agent": "Sage", "completed": False},
        ],
        morning_energy=5,
        morning_mood=6,
        morning_intention="Get through the day without overcommitting",
    )


# =============================================================================
# 4. API ROUTES
# =============================================================================

"""
These would live in backend/routes/checkin.py

The check-in flow is three steps:
  1. GET  /checkin/prepopulate/{type}  → Fetch context (Whoop, tasks, etc.)
  2. POST /checkin/extract             → Conversational extraction (optional)
  3. POST /checkin/confirm             → Save final values + trigger Council Round
"""

# from fastapi import APIRouter, Depends
# router = APIRouter(prefix="/checkin", tags=["checkin"])


# --- Step 1: Pre-populate ---
# @router.get("/prepopulate/am")
async def prepopulate_am():
    """Fetch Whoop + context data for the morning check-in UI."""
    # db = get_db()
    # today = date.today()
    # return await get_prepopulate_am(today, db)
    pass


# @router.get("/prepopulate/pm")
async def prepopulate_pm():
    """Fetch Whoop + tasks + skincare data for the evening check-in UI."""
    pass


# --- Step 2: Extract (conversational mode only) ---
# @router.post("/extract/am", response_model=CheckInAMExtractionResult)
async def extract_am(request: CheckInAMConversationalRequest):
    """
    Parse natural language into structured AM check-in values.
    Returns extracted values for user confirmation.
    Does NOT save anything yet.
    """
    result = await extract_checkin_am(request.raw_input)
    return result


# @router.post("/extract/pm", response_model=CheckInPMExtractionResult)
async def extract_pm(request: CheckInPMConversationalRequest):
    """Same for evening."""
    result = await extract_checkin_pm(request.raw_input)
    return result


# --- Step 3: Confirm + Save + Trigger Round ---
# @router.post("/confirm", response_model=CheckInResponse)
async def confirm_checkin(request: CheckInConfirmRequest):
    """
    Save the confirmed check-in values and trigger a Council Round.

    This is the endpoint that both conversational and quick-tap modes
    converge on. By this point, structured values are final.
    """
    # db = get_db()

    if request.checkin_type == "am":
        # Check for existing check-in today (prevent duplicates)
        # existing = db.query(CheckInAM).filter_by(date=request.date).first()
        # if existing and not request.is_backfill:
        #     raise HTTPException(409, "Morning check-in already exists for today")

        # Save check-in
        # checkin = CheckInAM(
        #     date=request.date,
        #     energy=request.energy,
        #     mood=request.mood,
        #     anxiety=request.anxiety,
        #     sleep_notes=request.sleep_notes,
        #     intention=request.intention,
        #     raw_input=request.raw_input,
        #     mode=request.mode.value,
        #     whoop_recovery=...,  # Snapshot current Whoop data
        # )
        # db.add(checkin)
        # db.flush()

        checkin_id = 42  # Placeholder

        # Trigger Council Round
        # from council_round_architecture import CouncilRoundService, RoundTrigger
        # service = CouncilRoundService(db)
        # round_result = await service.execute_round(
        #     trigger_type=RoundTrigger.CHECKIN_AM,
        #     trigger_data={
        #         "energy": request.energy,
        #         "mood": request.mood,
        #         "anxiety": request.anxiety,
        #         "sleep_notes": request.sleep_notes,
        #         "intention": request.intention,
        #     },
        #     trigger_reference_id=checkin_id,
        # )

        round_result = {"round_id": 1, "messages": []}  # Placeholder

    else:  # PM
        checkin_id = 43
        round_result = {"round_id": 2, "messages": []}

    # db.commit()

    return CheckInResponse(
        checkin_id=checkin_id,
        council_round_id=round_result["round_id"],
        council_messages=round_result["messages"],
    )


# =============================================================================
# 5. FRONTEND COMPONENT STRUCTURE
# =============================================================================

"""
React component hierarchy for the check-in flow.
All components in frontend/src/pages/checkin/ and frontend/src/components/checkin/

Pages:
  CheckInPage.tsx
    — Route: /checkin
    — Determines AM vs PM based on time of day (or lets user toggle)
    — Fetches prepopulate data on mount
    — Manages check-in state machine: input → extract → confirm → council response

Components:
  CheckInHeader.tsx
    — Shows Whoop context (pre-populated data)
    — "You slept 6h12m · Recovery 42% · HRV 38ms"
    — Optional tap to add sleep notes

  ConversationalInput.tsx
    — Aurore's prompt: "How are you this morning?"
    — Text area with warm placeholder
    — Submit sends to /checkin/extract/am
    — Handles follow-up questions from extraction

  QuickTapInput.tsx
    — Compact mode: emoji-scale rows for each metric
    — 5 faces per row, tap to select
    — Optional text fields for notes/intention
    — Bypasses extraction, sends directly to /checkin/confirm

  ExtractionConfirmation.tsx
    — Shows parsed values as tappable pills
    — "Energy 5 · Mood 6 · Anxiety 7"
    — Each pill is editable (tap to cycle value or open a slider)
    — Confirm button saves and triggers round

  CouncilResponsePanel.tsx
    — Appears after confirmation
    — Streams in Council Round messages (Aurore → agents)
    — Each message has agent avatar + name + text
    — Suggestion chips at the bottom for follow-up

  ModeToggle.tsx
    — Small toggle at top: "Talk to Aurore" / "Quick tap"
    — Switches between ConversationalInput and QuickTapInput
    — Remembers preference in localStorage

  BackfillBanner.tsx
    — Shown when previous day's check-in was missed
    — "You missed yesterday's check-in. Want to backfill?"
    — Tap opens a simplified version of the check-in for yesterday's date


STATE MACHINE:

  IDLE
    ↓ (user opens /checkin)
  PREPOPULATING
    ↓ (fetch Whoop + context from API)
  INPUT
    ↓ (conversational submit or quick-tap submit)
  EXTRACTING (conversational only)
    ↓ (extraction returns)
  CONFIRMING
    ↓ (user confirms values)
  SAVING
    ↓ (POST /checkin/confirm → triggers Council Round)
  COUNCIL_RESPONDING
    ↓ (stream in Council messages)
  COMPLETE
    ↓ (show summary + suggestion chips)


EXAMPLE FLOWS:

  Conversational (default):
    1. Open /checkin → see Whoop header (42% recovery, 6h12m sleep)
    2. Aurore asks: "How are you this morning?"
    3. Type: "Tired and anxious. Didn't sleep well."
    4. See extracted pills: Energy 4 · Mood 5 · Anxiety 7
    5. Adjust mood to 6 (tap pill, slide up)
    6. Aurore follows up: "What's one thing you want to focus on today?"
    7. Type: "Just get through the day"
    8. Confirm → saving → Council responds
    9. See Sage, Rex, Celeste responses below

  Quick-tap (low energy mornings):
    1. Open /checkin → see Whoop header
    2. Toggle to "Quick tap"
    3. Tap: Energy 😐 (4), Mood 🙂 (6), Anxiety 😰 (7)
    4. Skip intention (optional)
    5. Confirm → saving → Council responds
    6. See agent responses

  Backfill:
    1. Open /checkin → see backfill banner
    2. "You missed yesterday's evening check-in. Quick backfill?"
    3. Tap → simplified PM form for yesterday
    4. Fill in rough values → save (no Council Round for backfills)
    5. Continue to today's check-in
"""


# =============================================================================
# 6. STREAK TRACKING INTEGRATION
# =============================================================================

"""
The check-in confirm endpoint should also update HabitStreak records.

After saving a check-in:
  1. Query the "Check-ins" HabitStreak record
  2. If last_completed == yesterday → increment current_streak
  3. If last_completed < yesterday → reset current_streak to 1
  4. Update last_completed to today
  5. Update longest_streak if current > longest

This is lightweight enough to happen synchronously in the confirm endpoint.

For the skincare streak (owned by Celeste):
  - PM check-in with skincare_done=True updates the "Skincare" streak
  - Celeste references this streak in her Council Round responses

For the training streak (owned by Rex):
  - Updated when a Workout record is logged (separate endpoint)
  - Rex references this in morning check-in responses
"""


async def update_streaks_after_checkin(
    checkin_type: str,
    checkin_date: date,
    skincare_done: bool = False,
    db_session=None,
):
    """
    Update relevant habit streaks after a check-in is confirmed.
    """
    # --- Check-in streak ---
    # checkin_streak = db_session.query(HabitStreak).filter_by(habit_name="Check-ins").first()
    # if not checkin_streak:
    #     checkin_streak = HabitStreak(habit_name="Check-ins", current_streak=0, longest_streak=0)
    #     db_session.add(checkin_streak)
    #
    # if checkin_streak.last_completed == checkin_date - timedelta(days=1):
    #     checkin_streak.current_streak += 1
    # elif checkin_streak.last_completed != checkin_date:  # Don't double-count same day
    #     checkin_streak.current_streak = 1
    #
    # checkin_streak.last_completed = checkin_date
    # checkin_streak.longest_streak = max(checkin_streak.longest_streak, checkin_streak.current_streak)

    # --- Skincare streak (PM only) ---
    # if checkin_type == "pm" and skincare_done:
    #     skincare_streak = db_session.query(HabitStreak).filter_by(habit_name="Skincare").first()
    #     # Same logic as above
    pass


# =============================================================================
# 7. SMART NOTIFICATION TIMING (Phase 2+, design now)
# =============================================================================

"""
When notifications are implemented, check-in prompts should be
time-aware based on Whoop data:

MORNING:
  - Whoop knows approximate wake time from sleep data
  - Prompt arrives ~5 minutes after detected wake
  - Fallback: 7:00 AM if no Whoop data
  - Don't prompt before 5:30 AM even if Whoop says they woke

EVENING:
  - Whoop knows typical bedtime from sleep patterns
  - Prompt arrives ~30 minutes before average bedtime
  - Fallback: 9:00 PM if no Whoop data
  - If PM check-in not done by 10:30 PM, send a gentle final nudge

MISSED CHECK-IN:
  - If morning check-in isn't done by 12:00 PM, Sage sends a
    casual nudge in the Council Chat (not a notification):
    "Hey — no morning check-in today. No stress, but I'm here if
     you want to log one before the day gets away from you."
  - This is a proactive round trigger, not a notification.

ADAPTIVE TIMING:
  - Track which prompt times get the fastest response
  - Gradually adjust toward the user's natural response window
  - e.g. if Shay consistently checks in at 6:45 AM, prompt at 6:40
"""
