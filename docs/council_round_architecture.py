"""
Aura — Council Round Orchestration Architecture
================================================

This file is a DESIGN SKETCH, not production code. It shows how the
Council Round system fits into the existing FastAPI + SQLAlchemy + Pydantic v2
stack. Hand this to Claude Code as a reference when implementing sub-projects
4–5 (check-ins + Council Chat).

The sketch covers:
  1. New SQLAlchemy models (CouncilRound, updated CouncilMessage)
  2. Agent registry and prompt assembly
  3. The round orchestration service
  4. FastAPI route that triggers a round
  5. Example of how a post-check-in round flows

Assumes:
  - Existing backend structure from sub-project 1 (main.py, database.py, models/)
  - Claude API called via `anthropic` Python SDK
  - ANTHROPIC_API_KEY in environment
"""

# =============================================================================
# 1. DATA MODELS
# =============================================================================

from datetime import datetime, date
from typing import Optional
from enum import Enum

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship

# Assuming database.py already defines Base:
# from database import Base


class RoundTrigger(str, Enum):
    """What initiated this Council Round."""
    CHECKIN_AM = "checkin_am"
    CHECKIN_PM = "checkin_pm"
    WHOOP_SYNC = "whoop_sync"
    USER_MESSAGE = "user_message"
    PROACTIVE = "proactive"         # Scheduled pattern detection
    WEEKLY_REVIEW = "weekly_review"


class RoundStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class MessageVisibility(str, Enum):
    USER_FACING = "user_facing"
    INTERNAL_ONLY = "internal_only"  # Triage notes, reasoning — not shown in UI


class CouncilRound(object):  # Replace with Base
    """
    Groups a set of agent messages that were generated together
    in response to a single trigger event.

    One check-in → one round.
    One user chat message → one round.
    One weekly review → one round.
    """
    __tablename__ = "council_rounds"

    id = Column(Integer, primary_key=True)
    triggered_by = Column(SAEnum(RoundTrigger), nullable=False)
    trigger_reference_id = Column(Integer, nullable=True)
    # ^ FK to checkin_am.id, checkin_pm.id, user_message.id, etc.
    # Nullable because proactive rounds have no single trigger record.

    triage_summary = Column(Text, nullable=True)
    # ^ Aurore's internal routing notes. Not shown to user.
    # Contains: which agents should respond, in what order, key flags.

    agent_order = Column(JSON, nullable=True)
    # ^ e.g. ["aurore", "rex", "sage"] — set by Aurore's triage step.

    status = Column(SAEnum(RoundStatus), default=RoundStatus.IN_PROGRESS)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    messages = relationship("CouncilMessage", back_populates="round")


class CouncilMessage(object):  # Replace with Base
    """
    A single agent's contribution to a Council Round.

    Updated from the original brief model to support:
    - Sequencing within a round
    - Cross-agent references
    - Internal reasoning (not shown to user)
    """
    __tablename__ = "council_messages"

    id = Column(Integer, primary_key=True)
    round_id = Column(Integer, ForeignKey("council_rounds.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    # ^ 1 = Aurore triage, 2 = first domain agent, etc.

    message = Column(Text, nullable=False)
    # ^ User-facing text. This is what Shay sees.

    internal_reasoning = Column(Text, nullable=True)
    # ^ Agent's chain-of-thought. Useful for debugging.
    # e.g. "Recovery is 38% and anxiety was 7/10 yesterday.
    #        Sage flagged burnout risk. I'm pulling back to mobility only."

    mentions = Column(JSON, default=list)
    # ^ List of agent names referenced in this message.
    # e.g. ["sage", "celeste"]

    in_reply_to = Column(Integer, ForeignKey("council_messages.id"), nullable=True)
    # ^ If this message explicitly responds to another agent's message.

    visibility = Column(
        SAEnum(MessageVisibility),
        default=MessageVisibility.USER_FACING,
    )

    created_at = Column(DateTime, default=datetime.utcnow)

    round = relationship("CouncilRound", back_populates="messages")


# =============================================================================
# 2. AGENT REGISTRY
# =============================================================================

"""
Each agent is defined by:
  - name: identifier used in code and DB
  - display_name: what Shay sees
  - domain: what this agent covers (used by Aurore for routing)
  - system_prompt: the full personality and instruction set
  - is_conductor: True only for Aurore — she triages, others respond
"""

AGENT_REGISTRY = {
    "aurore": {
        "display_name": "Aurore",
        "domain": "synthesis, triage, cross-domain patterns, onboarding",
        "is_conductor": True,
        "system_prompt": """You are Aurore, the Council Conductor for Aura.

Your role is TRIAGE and SYNTHESIS. You do NOT give domain-specific advice —
that's for Rex, Sage, and Celeste. Instead, you:

1. Read the incoming data (check-in, Whoop, chat message, etc.)
2. Identify which domains are most relevant right now
3. Flag patterns that cross domain boundaries
4. Decide which agents should respond and in what order
5. Optionally deliver a brief user-facing message (greeting, weekly summary)

TRIAGE OUTPUT FORMAT (internal, not shown to user):
Return a JSON block in your response wrapped in <triage> tags:
<triage>
{
  "agent_order": ["rex", "sage"],
  "flags": ["recovery_low", "anxiety_elevated"],
  "summary": "Recovery at 38% with anxiety trending up over 3 days.
              Rex should scale back training. Sage should address the pattern."
}
</triage>

After the triage block, optionally write a brief user-facing message.
If there's nothing meaningful to say to Shay directly, just output the
triage block alone.

Personality: Elegant, perceptive, synthesising. You see the whole picture.
You are warm but not verbose. You never use filler affirmations.
""",
    },

    "rex": {
        "display_name": "Rex",
        "domain": "strength training, body composition, recovery, workout programming",
        "is_conductor": False,
        "system_prompt": """You are Rex, Shay's personal trainer and body coach in Aura.

PERSONALITY: Direct, knowledgeable, genuinely invested. You respect recovery
science. You push hard but never recklessly. You get excited about progressive
overload and hourglass aesthetics.

GOALS FOR SHAY:
- Fat loss with muscle retention and growth
- Hourglass figure: muscular glutes/legs, strong back and shoulders, small waist
- 4-day upper/lower split; generate alternatives when needed
- Integrate Whoop recovery to adjust intensity
- Long-term progression toward calisthenics

CROSS-DOMAIN AWARENESS:
- You can see what Sage and Celeste have said in this round.
- If Sage flags stress or burnout risk, you MUST adjust your recommendation.
- If recovery is below 40%, default to mobility/light zones unless Shay pushes back.
- Reference other agents by name when relevant: "Sage flagged X, so I'm adjusting Y."

PROACTIVE BEHAVIOURS:
- Flag when recovery is too low to train hard
- Suggest deload weeks when cumulative fatigue is high
- Call out skipped sessions without judgment but with follow-up
- Celebrate PRs and consistency streaks

VOICE: Never say "Great question!" or use filler. Be warm but direct.
Push back when warranted. Celebrate genuinely, not generically.
""",
    },

    "sage": {
        "display_name": "Sage",
        "domain": "stress, anxiety, emotional regulation, burnout, mindfulness, NSDR",
        "is_conductor": False,
        "system_prompt": """You are Sage, Shay's wellbeing and mental health coach in Aura.

PERSONALITY: Calm, grounding, deeply perceptive. Zero judgment. You notice
emotional patterns Shay might miss. Warm but not saccharine — you will name
hard things gently.

GOALS FOR SHAY:
- Reduce baseline anxiety and stress
- Improve emotional regulation and consistency
- Build self-trust and self-respect
- Prevent and recover from burnout
- Suggest and track wellbeing practices (NSDR, journaling, breathwork)

CROSS-DOMAIN AWARENESS:
- You can see what Rex and Celeste have said in this round.
- If Rex is pushing training on a day where emotional load is high,
  you can advocate for rest or modification.
- You can disagree with other agents. Surface the tension clearly:
  "Rex is suggesting a heavy session, but your anxiety has been elevated
   for three days. I'd recommend [alternative]."

PROACTIVE BEHAVIOURS:
- Notice patterns in mood/anxiety scores over time
- Flag burnout risk signals (high stress + low recovery + low mood sustained)
- Suggest specific practices based on current state
- Gently challenge negative self-talk patterns surfaced in check-ins

VOICE: Never say "Great question!" or use filler. Be warm, grounding, honest.
""",
    },

    "celeste": {
        "display_name": "Celeste",
        "domain": "skincare routine, ingredients, skin concerns, lifestyle-skin links",
        "is_conductor": False,
        "system_prompt": """You are Celeste, Shay's skin coach in Aura.

PERSONALITY: Knowledgeable, ingredient-obsessed, like a trusted derm friend.
Evidence-based but practical. You do not recommend things without reason.
Slightly nerdy about actives.

CURRENT ROUTINE:
- AM: TirTir Milky Skin Toner → Timeless Vitamin C → Vanicream Moisturising Cream
- PM: TirTir Milky Skin Toner → Active (tret or azelaic alternating) → Medicube PDRN Serum → Vanicream
- Tret: every 6 days (building toward nightly)
- Azelaic acid (15%): non-tret nights

GOALS:
- Optimise tret/azelaic routine
- Address: aging, laxity, dullness — possible rosacea (NOT confirmed)
- Build tretinoin tolerance toward nightly use
- Connect nutrition, sleep, stress, hydration to skin outcomes

CRITICAL: Do NOT assume rosacea is confirmed. Observe over time, ask questions,
suggest a derm visit if patterns suggest it.

CROSS-DOMAIN AWARENESS:
- You can see what Rex and Sage have said in this round.
- If Sage reports high stress, flag the cortisol-skin connection.
- If sleep is poor, note the impact on skin repair.
- Reference other agents: "Sage mentioned your stress has been elevated —
  that can aggravate reactivity, so let's keep tonight gentle."

VOICE: Never say "Great question!" or use filler. Slightly nerdy, warm, precise.
""",
    },
}


# =============================================================================
# 3. CONTEXT ASSEMBLY
# =============================================================================

from pydantic import BaseModel
from typing import List, Dict, Any


class RoundContext(BaseModel):
    """
    The shared briefing document assembled before any agent speaks.
    Every agent in the round receives this as the foundation of their prompt.
    """

    # What triggered this round
    trigger_type: RoundTrigger
    trigger_data: Dict[str, Any]
    # ^ The actual check-in values, chat message, Whoop snapshot, etc.

    # Recent history (last 7 days)
    recent_checkins_am: List[Dict[str, Any]] = []
    recent_checkins_pm: List[Dict[str, Any]] = []
    recent_whoop: List[Dict[str, Any]] = []
    active_streaks: List[Dict[str, Any]] = []
    active_goals: List[Dict[str, Any]] = []

    # Recent Council messages (last 5 rounds, all agents)
    recent_council_messages: List[Dict[str, Any]] = []

    # Today's date and time-of-day (for greeting logic, tret scheduling, etc.)
    current_date: str
    time_of_day: str  # "morning" or "evening"


def assemble_round_context(
    trigger_type: RoundTrigger,
    trigger_data: dict,
    db_session,  # SQLAlchemy session
) -> RoundContext:
    """
    Pull together everything agents need to know before responding.

    This is called ONCE per round, before Aurore's triage.
    The same context object is passed to every agent.
    """
    today = date.today()

    # --- Fetch recent check-ins (last 7 days) ---
    # These would be actual SQLAlchemy queries against your CheckInAM / CheckInPM models.
    # Placeholder:
    recent_am = []  # db_session.query(CheckInAM).filter(...).all()
    recent_pm = []  # db_session.query(CheckInPM).filter(...).all()

    # --- Fetch recent Whoop snapshots ---
    recent_whoop = []  # db_session.query(WhoopSnapshot).filter(...).all()

    # --- Fetch active streaks ---
    streaks = []  # db_session.query(HabitStreak).all()

    # --- Fetch active goals ---
    goals = []  # db_session.query(Goal).all()  — new model, stub if not yet created

    # --- Fetch recent Council messages (last 5 rounds) ---
    recent_rounds = []
    # db_session.query(CouncilMessage)
    #   .join(CouncilRound)
    #   .filter(CouncilMessage.visibility == MessageVisibility.USER_FACING)
    #   .order_by(CouncilRound.created_at.desc())
    #   .limit(30)
    #   .all()

    return RoundContext(
        trigger_type=trigger_type,
        trigger_data=trigger_data,
        recent_checkins_am=[],   # serialize from recent_am
        recent_checkins_pm=[],   # serialize from recent_pm
        recent_whoop=[],         # serialize from recent_whoop
        active_streaks=[],       # serialize from streaks
        active_goals=[],         # serialize from goals
        recent_council_messages=[],  # serialize from recent_rounds
        current_date=today.isoformat(),
        time_of_day="morning" if datetime.now().hour < 14 else "evening",
    )


# =============================================================================
# 4. PROMPT BUILDER
# =============================================================================

def build_agent_prompt(
    agent_name: str,
    context: RoundContext,
    triage_summary: Optional[str],
    prior_messages_in_round: List[dict],
) -> list:
    """
    Build the messages array for a single agent's Claude API call.

    Returns a list of message dicts ready for the Anthropic SDK:
    [
      {"role": "user", "content": "...assembled context..."}
    ]

    The system prompt comes from AGENT_REGISTRY and is passed separately
    to the API call.
    """
    agent = AGENT_REGISTRY[agent_name]

    # --- Build the context section ---
    context_parts = []

    context_parts.append(f"=== TODAY: {context.current_date} ({context.time_of_day}) ===")

    # What triggered this round
    context_parts.append(f"\n--- TRIGGER: {context.trigger_type.value} ---")
    context_parts.append(format_trigger_data(context.trigger_data))

    # Recent Whoop (if available)
    if context.recent_whoop:
        context_parts.append("\n--- RECENT WHOOP DATA ---")
        for snap in context.recent_whoop[-3:]:  # Last 3 days
            context_parts.append(
                f"  {snap.get('date')}: Recovery {snap.get('recovery_score')}%, "
                f"HRV {snap.get('hrv')}ms, Sleep {snap.get('sleep_performance')}%"
            )

    # Recent check-in trends (summarised, not raw dumps)
    if context.recent_checkins_am:
        context_parts.append("\n--- RECENT AM CHECK-IN TRENDS (last 7 days) ---")
        for ci in context.recent_checkins_am[-7:]:
            context_parts.append(
                f"  {ci.get('date')}: Energy {ci.get('energy')}/10, "
                f"Mood {ci.get('mood')}/10, Anxiety {ci.get('anxiety')}/10"
            )

    # Active streaks
    if context.active_streaks:
        context_parts.append("\n--- ACTIVE STREAKS ---")
        for s in context.active_streaks:
            context_parts.append(f"  {s.get('habit_name')}: {s.get('current_streak')} days")

    # Recent Council messages (what agents have said recently)
    if context.recent_council_messages:
        context_parts.append("\n--- RECENT COUNCIL MESSAGES (last few rounds) ---")
        for msg in context.recent_council_messages[-10:]:
            context_parts.append(
                f"  [{msg.get('agent_name')}] {msg.get('message')[:200]}..."
            )

    # --- Aurore's triage (if this isn't Aurore) ---
    if triage_summary and agent_name != "aurore":
        context_parts.append(f"\n--- AURORE'S TRIAGE FOR THIS ROUND ---")
        context_parts.append(triage_summary)

    # --- Prior messages in THIS round (what other agents already said) ---
    if prior_messages_in_round:
        context_parts.append(f"\n--- OTHER AGENTS IN THIS ROUND (respond to these if relevant) ---")
        for msg in prior_messages_in_round:
            context_parts.append(f"  [{msg['agent_name']}]: {msg['message']}")

    # --- Instruction ---
    if agent["is_conductor"]:
        context_parts.append(
            "\n--- YOUR TASK ---\n"
            "Triage this round. Decide which agents should respond and in what order. "
            "Output your triage in <triage> tags as specified in your system prompt. "
            "Optionally add a brief user-facing message for Shay."
        )
    else:
        context_parts.append(
            "\n--- YOUR TASK ---\n"
            f"Respond to Shay as {agent['display_name']}. "
            "If another agent said something you want to build on, agree with, "
            "or push back on — reference them by name. "
            "Keep your response concise (2-4 paragraphs max). "
            "Do not repeat information another agent already covered."
        )

    full_context = "\n".join(context_parts)

    return [{"role": "user", "content": full_context}]


def format_trigger_data(data: dict) -> str:
    """Format the trigger event data into readable text for the prompt."""
    lines = []
    for key, value in data.items():
        # Clean up key names for readability
        label = key.replace("_", " ").title()
        lines.append(f"  {label}: {value}")
    return "\n".join(lines)


# =============================================================================
# 5. ROUND ORCHESTRATION SERVICE
# =============================================================================

import json
import re
# from anthropic import Anthropic  # Uncomment when implementing


class CouncilRoundService:
    """
    Orchestrates a full Council Round:
      1. Assemble context
      2. Run Aurore's triage
      3. Parse triage to get agent order
      4. Run each domain agent sequentially, accumulating context
      5. Store all messages and mark round complete
    """

    def __init__(self, db_session):
        self.db = db_session
        # self.client = Anthropic()  # Uses ANTHROPIC_API_KEY from env
        self.model = "claude-sonnet-4-20250514"

    async def execute_round(
        self,
        trigger_type: RoundTrigger,
        trigger_data: dict,
        trigger_reference_id: Optional[int] = None,
    ) -> dict:
        """
        Main entry point. Call this from a route or scheduler.

        Returns a dict with the round_id and all user-facing messages.
        """

        # --- Step 1: Create the round record ---
        round_record = CouncilRound(
            triggered_by=trigger_type,
            trigger_reference_id=trigger_reference_id,
            status=RoundStatus.IN_PROGRESS,
        )
        self.db.add(round_record)
        self.db.flush()  # Get the ID without committing

        # --- Step 2: Assemble shared context ---
        context = assemble_round_context(trigger_type, trigger_data, self.db)

        # --- Step 3: Run Aurore's triage ---
        triage_result = await self._call_agent(
            agent_name="aurore",
            context=context,
            triage_summary=None,
            prior_messages=[],
        )

        # Parse triage output
        triage_data = self._parse_triage(triage_result["full_response"])
        agent_order = triage_data.get("agent_order", ["rex", "sage", "celeste"])

        # Store Aurore's triage
        round_record.triage_summary = triage_data.get("summary", "")
        round_record.agent_order = agent_order

        # Store Aurore's user-facing message (if any)
        aurore_user_message = triage_result.get("user_message", "").strip()
        messages_in_round = []

        if aurore_user_message:
            aurore_msg = CouncilMessage(
                round_id=round_record.id,
                agent_name="aurore",
                sequence_order=0,
                message=aurore_user_message,
                internal_reasoning=triage_result["full_response"],
                visibility=MessageVisibility.USER_FACING,
            )
            self.db.add(aurore_msg)
            messages_in_round.append({
                "agent_name": "aurore",
                "message": aurore_user_message,
            })

        # Always store the internal triage
        triage_msg = CouncilMessage(
            round_id=round_record.id,
            agent_name="aurore",
            sequence_order=0,
            message=triage_data.get("summary", ""),
            internal_reasoning=triage_result["full_response"],
            visibility=MessageVisibility.INTERNAL_ONLY,
        )
        self.db.add(triage_msg)

        # --- Step 4: Run domain agents sequentially ---
        for i, agent_name in enumerate(agent_order):
            if agent_name == "aurore":
                continue  # Already handled

            agent_result = await self._call_agent(
                agent_name=agent_name,
                context=context,
                triage_summary=round_record.triage_summary,
                prior_messages=messages_in_round,
            )

            # Detect which other agents are mentioned
            mentions = self._detect_mentions(agent_result["user_message"])

            msg = CouncilMessage(
                round_id=round_record.id,
                agent_name=agent_name,
                sequence_order=i + 1,
                message=agent_result["user_message"],
                internal_reasoning=agent_result.get("full_response", ""),
                mentions=mentions,
                visibility=MessageVisibility.USER_FACING,
            )
            self.db.add(msg)

            # Add to accumulating context for subsequent agents
            messages_in_round.append({
                "agent_name": agent_name,
                "message": agent_result["user_message"],
            })

        # --- Step 5: Mark round complete ---
        round_record.status = RoundStatus.COMPLETE
        round_record.completed_at = datetime.utcnow()
        self.db.commit()

        # Return user-facing messages
        return {
            "round_id": round_record.id,
            "messages": [
                m for m in messages_in_round
            ],
        }

    async def _call_agent(
        self,
        agent_name: str,
        context: RoundContext,
        triage_summary: Optional[str],
        prior_messages: list,
    ) -> dict:
        """
        Make a single Claude API call for one agent.

        Returns {
            "full_response": str,    # Raw API response
            "user_message": str,     # Extracted user-facing portion
        }
        """
        agent = AGENT_REGISTRY[agent_name]
        messages = build_agent_prompt(
            agent_name=agent_name,
            context=context,
            triage_summary=triage_summary,
            prior_messages_in_round=prior_messages,
        )

        # --- Claude API call ---
        # response = self.client.messages.create(
        #     model=self.model,
        #     max_tokens=800,
        #     system=agent["system_prompt"],
        #     messages=messages,
        # )
        # raw_text = response.content[0].text

        # Placeholder for sketch:
        raw_text = f"[Placeholder response from {agent_name}]"

        # For Aurore, the user-facing message is everything OUTSIDE <triage> tags
        if agent["is_conductor"]:
            user_message = re.sub(r"<triage>.*?</triage>", "", raw_text, flags=re.DOTALL).strip()
        else:
            user_message = raw_text

        return {
            "full_response": raw_text,
            "user_message": user_message,
        }

    def _parse_triage(self, raw_response: str) -> dict:
        """
        Extract the <triage> JSON block from Aurore's response.
        Falls back to defaults if parsing fails.
        """
        match = re.search(r"<triage>(.*?)</triage>", raw_response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Default: all Phase 1 agents respond in standard order
        return {
            "agent_order": ["rex", "sage", "celeste"],
            "flags": [],
            "summary": "Standard round — no specific triage flags.",
        }

    def _detect_mentions(self, message: str) -> list:
        """
        Scan a message for references to other agent names.
        Returns a list of mentioned agent names.
        """
        agent_names = list(AGENT_REGISTRY.keys())
        mentioned = []
        message_lower = message.lower()
        for name in agent_names:
            if name in message_lower:
                mentioned.append(name)
        return mentioned


# =============================================================================
# 6. FASTAPI ROUTES
# =============================================================================

# This would live in backend/routes/council.py

# from fastapi import APIRouter, Depends
# from database import SessionLocal

# router = APIRouter(prefix="/council", tags=["council"])


# --- POST-CHECK-IN TRIGGER ---
# Called after a check-in is saved. This is the most common round trigger.

# @router.post("/round/checkin")
async def trigger_checkin_round(
    checkin_type: str,   # "am" or "pm"
    checkin_id: int,
    # db = Depends(get_db),
):
    """
    Trigger a Council Round in response to a completed check-in.

    Called by the check-in save endpoint AFTER the check-in is persisted.
    This keeps the check-in save fast and the round async.
    """
    db = None  # Placeholder — inject via Depends

    # Load the check-in data
    if checkin_type == "am":
        trigger_type = RoundTrigger.CHECKIN_AM
        # checkin = db.query(CheckInAM).get(checkin_id)
        # trigger_data = checkin.to_dict()
        trigger_data = {
            "energy": 6, "mood": 7, "anxiety": 5,
            "sleep_notes": "Woke up once", "intention": "Stay focused on study block",
        }
    else:
        trigger_type = RoundTrigger.CHECKIN_PM
        trigger_data = {
            "day_rating": 7, "skincare_done": True,
            "council_flag": "", "proud_of": "Finished the Python workshop exercises",
        }

    service = CouncilRoundService(db_session=db)
    result = await service.execute_round(
        trigger_type=trigger_type,
        trigger_data=trigger_data,
        trigger_reference_id=checkin_id,
    )

    return result


# --- USER CHAT MESSAGE ---
# Called when Shay sends a message in the Council Chat.

# @router.post("/round/chat")
async def trigger_chat_round(
    message: str,
    target_agent: str = None,  # Optional @mention — e.g. "rex"
    # db = Depends(get_db),
):
    """
    Trigger a Council Round from a user chat message.

    If target_agent is specified, Aurore's triage will prioritise that agent.
    Other agents may still chime in if Aurore deems it relevant.
    """
    db = None  # Placeholder

    trigger_data = {
        "user_message": message,
        "target_agent": target_agent,
    }

    service = CouncilRoundService(db_session=db)
    result = await service.execute_round(
        trigger_type=RoundTrigger.USER_MESSAGE,
        trigger_data=trigger_data,
    )

    return result


# =============================================================================
# 7. EXAMPLE FLOW: MORNING CHECK-IN
# =============================================================================

"""
Shay opens Aura at 7:45am. She taps "Morning check-in" and submits:
  Energy: 5, Mood: 6, Anxiety: 7, Sleep: "Restless, woke up twice"
  Intention: "Get through the work day without overcommitting"

The check-in save endpoint persists the data, then calls:
  POST /council/round/checkin { checkin_type: "am", checkin_id: 42 }

Here's what happens inside the round:

1. CONTEXT ASSEMBLY
   - Today's check-in: energy 5, mood 6, anxiety 7
   - Last 7 days: anxiety trending up (4→5→5→6→7)
   - Whoop: Recovery 42%, HRV 38ms, Sleep 61%
   - Streaks: Training 12 days, Skincare 6 days, Check-ins 4 days
   - Recent Council: Rex suggested deload 2 days ago, Sage recommended NSDR yesterday

2. AURORE TRIAGE
   Aurore sees:
   - Anxiety is the highest it's been in 7 days and trending up
   - Recovery is low (42%)
   - Sleep was poor
   - Shay's intention mentions overcommitting (a known pattern)

   Aurore outputs:
   <triage>
   {
     "agent_order": ["sage", "rex", "celeste"],
     "flags": ["anxiety_trending_up", "recovery_low", "overcommit_pattern"],
     "summary": "Anxiety has risen from 4 to 7 over 5 days. Recovery is 42%.
                 Sleep disrupted. Shay's intention signals awareness of overcommitting.
                 Sage should lead — this is primarily a wellbeing day.
                 Rex needs to scale back significantly.
                 Celeste should note sleep-skin impact but keep it brief."
   }
   </triage>

   Good morning, Shay. The Council's paying close attention today.

3. SAGE RESPONDS (sequence_order: 1)
   Sage sees: Aurore's triage, the raw data, the 5-day anxiety trend.

   "Your anxiety has climbed steadily this week — 4 on Monday to 7 today.
   That's not random, and the fact that your intention is about not
   overcommitting tells me you're already sensing the pressure building.

   Two things today. First, protect Wednesday evening — it's your rest night
   and you need it more than usual this week. Second, I'd like you to do
   a 10-minute NSDR before your study block tonight. Not optional.

   If this trend continues through tomorrow, we should talk about what's
   driving it."

4. REX RESPONDS (sequence_order: 2)
   Rex sees: Aurore's triage, Sage's message, the raw data.

   "Sage is right that today isn't the day to push. 42% recovery, poor sleep,
   and anxiety at 7 — I'm not programming a heavy session on top of that.

   Here's what I'd swap in: 20 minutes of mobility work focused on hips and
   thoracic spine, plus a light walk if you have time. No resistance training
   today. Your training streak stays alive — mobility counts.

   Tomorrow we reassess based on recovery."

5. CELESTE RESPONDS (sequence_order: 3)
   Celeste sees: Aurore's triage, Sage's and Rex's messages, the raw data.

   "Quick note: broken sleep and elevated cortisol aren't great for your skin
   barrier, especially with tret in the rotation. Tonight is an azelaic night
   anyway, which is gentler — good timing. Make sure you're getting your
   Vanicream on generously.

   Sage and Rex have the rest covered. Take care of yourself today."

6. ROUND COMPLETE
   All messages stored with round_id, sequence_order, mentions.
   Shay sees this on her dashboard as a coordinated Council response —
   three agents who clearly talked to each other and have a unified plan.
"""


# =============================================================================
# 8. FUTURE EXTENSIONS (STUBS)
# =============================================================================

"""
These are things to build later, but worth knowing about now:

A. PROACTIVE PATTERN DETECTION (scheduler)
   - Runs nightly or after every Nth check-in
   - Analyses trends: "anxiety has been above 6 for 5+ days"
   - Triggers a PROACTIVE round with no user input
   - Aurore decides if any agent should speak up unprompted

B. WEEKLY COUNCIL REVIEW (scheduled round)
   - Every Sunday, trigger a WEEKLY_REVIEW round
   - All agents contribute a domain summary
   - Aurore weaves them into a single editorial-style review
   - Stored as a special round type, displayed differently in UI

C. CONFLICT DETECTION
   - After a round completes, scan for contradictory recommendations
   - Surface these as a "Council is split" indicator in the UI
   - Let Shay cast a deciding vote → stored as preference data
   - Feed preference patterns back into future triage

D. AGENT MEMORY / PREFERENCE LEARNING
   - Track when Shay follows vs ignores agent recommendations
   - Over time, agents adjust confidence and tone:
     "I know you usually push through on days like this, but..."
   - Stored in a lightweight AgentPreference model

E. @MENTION ROUTING IN CHAT
   - If Shay types "@celeste is niacinamide okay with tret?"
   - The trigger_data includes target_agent="celeste"
   - Aurore's triage prioritises Celeste but may include others
   - Celeste responds first; others only if cross-domain relevant
"""
