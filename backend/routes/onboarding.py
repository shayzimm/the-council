import json
from datetime import datetime, timezone
from typing import Optional

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from agents.registry import get_agent, get_introduction_prompt
from database import get_db
from models import CouncilMessage, CouncilRound, Goal, UserProfile

router = APIRouter(prefix="/onboarding")

client = anthropic.Anthropic()

CLAUDE_MODEL = "claude-sonnet-4-20250514"

AGENT_ORDER = ["aurore", "rex", "sage", "celeste"]

WELCOME_MESSAGE = (
    "Hi Shay. I\u2019m Aurore \u2014 I coordinate The Council, your personal advisory "
    "team. Before I introduce everyone, I\u2019d love to understand you a little. "
    "This takes about five minutes, and you can always update things later."
)

EXTRACTION_PROMPTS: dict[str, str] = {
    "lifestyle": (
        "You extract structured profile data from a natural conversational response.\n\n"
        "The user (Shay) is describing her typical week. Extract:\n"
        "- training_frequency: number of sessions per week (integer)\n"
        "- training_type: brief description (e.g. \"upper/lower split\", \"PPL\", \"CrossFit\")\n"
        '- training_experience: "beginner" | "intermediate" | "advanced" (infer from context)\n'
        '- work_status: "full_time" | "part_time" | "casual" | "not_working" | null\n'
        '- study_status: "full_time" | "part_time" | null\n'
        "- location: city/region if mentioned, null otherwise\n\n"
        "Set fields to null if not mentioned. Do not infer values that aren't at least implied.\n\n"
        "RESPOND ONLY WITH JSON. No preamble, no markdown."
    ),
    "skin": (
        "You extract structured profile data from a natural conversational response.\n\n"
        "The user (Shay) is describing her skin and skincare routine. Extract:\n"
        '- skin_type: "dry" | "oily" | "combination" | "normal" | "sensitive" | null\n'
        '- skin_concerns: array of strings (e.g. ["aging", "dullness", "possible rosacea"]), empty array if none mentioned\n'
        "- current_routine_brief: brief text summary of their routine, null if not described\n"
        '- active_medications: array of strings (e.g. ["tretinoin 0.025%", "azelaic acid 15%"]), empty array if none mentioned\n\n'
        "Set fields to null if not mentioned. Do not infer values that aren't at least implied.\n\n"
        "RESPOND ONLY WITH JSON. No preamble, no markdown."
    ),
    "wellbeing": (
        "You extract structured profile data from a natural conversational response.\n\n"
        "The user (Shay) is describing her mental health and wellbeing. Extract:\n"
        "- stress_baseline: integer 1-10 (self-assessment), null if not mentioned\n"
        "- anxiety_baseline: integer 1-10, null if not mentioned\n"
        "- sleep_baseline: integer 1-10, null if not mentioned\n"
        "- energy_baseline: integer 1-10, null if not mentioned\n\n"
        'Interpret qualitative descriptions into numbers when possible (e.g. "pretty stressed" '
        'might be 7, "sleep is ok" might be 5-6). Set to null if truly not mentioned.\n\n'
        "RESPOND ONLY WITH JSON. No preamble, no markdown."
    ),
    "other": (
        "You extract additional profile data from a natural conversational response.\n\n"
        "The user (Shay) is sharing additional context. Extract:\n"
        '- supplements: array of strings (e.g. ["magnesium", "vitamin D"]), empty array if none\n'
        "- cycle_length: integer (days), null if not mentioned\n"
        "- cycle_tracking: boolean, null if not mentioned\n"
        "- additional_notes: any other relevant information as a string, null if nothing notable\n\n"
        "Set fields to null if not mentioned. Do not infer values that aren't at least implied.\n\n"
        "RESPOND ONLY WITH JSON. No preamble, no markdown."
    ),
}

GOAL_EXTRACTION_PROMPT = (
    "You extract goals from a natural conversational response about what the user wants to achieve.\n\n"
    "For each goal mentioned, extract:\n"
    "- title: concise goal statement\n"
    '- domain: "training" | "skin" | "wellbeing" | "nutrition" | "general"\n'
    '- goal_type: "north_star" (qualitative/long-term) or "milestone" (measurable/time-bound)\n'
    "- target_value: number if mentioned, null otherwise\n"
    '- target_unit: unit if mentioned ("kg", "days", "%"), null otherwise\n'
    "- deadline: ISO date string if mentioned, null otherwise\n"
    '- linked_agent: which agent owns this ("rex", "sage", "celeste", "aurore")\n\n'
    "Return a JSON array of goals. If no clear goals are mentioned, return an empty array.\n"
    "Users often state goals vaguely. Extract what you can and note what's vague.\n\n"
    "RESPOND ONLY WITH JSON. No preamble, no markdown."
)

GOAL_TOPIC_DOMAIN_MAP: dict[str, str] = {
    "lifestyle_goals": "training",
    "skin_goals": "skin",
    "wellbeing_goals": "wellbeing",
}

PROFILE_TOPICS = {"lifestyle", "skin", "wellbeing", "other"}
GOAL_TOPICS = {"lifestyle_goals", "skin_goals", "wellbeing_goals"}
ALL_TOPICS = PROFILE_TOPICS | GOAL_TOPICS

# Profile field mapping per topic — which UserProfile columns each topic can update
TOPIC_PROFILE_FIELDS: dict[str, list[str]] = {
    "lifestyle": [
        "training_frequency",
        "training_type",
        "training_experience",
        "work_status",
        "study_status",
        "location",
    ],
    "skin": [
        "skin_type",
        "skin_concerns",
        "current_routine_brief",
        "active_medications",
    ],
    "wellbeing": [
        "stress_baseline",
        "anxiety_baseline",
        "sleep_baseline",
        "energy_baseline",
    ],
    "other": [
        "supplements",
        "cycle_length",
        "cycle_tracking",
    ],
}


# ---------------------------------------------------------------------------
# Pydantic request / response schemas
# ---------------------------------------------------------------------------


class StartResponse(BaseModel):
    profile_id: int
    welcome_message: str


class ExtractRequest(BaseModel):
    topic: str
    raw_input: str


class ExtractResponse(BaseModel):
    extracted_data: dict | list


class ConfirmTopicRequest(BaseModel):
    topic: str
    extracted_data: dict
    goals: Optional[list[dict]] = None


class ConfirmTopicResponse(BaseModel):
    success: bool
    topic: str


class CompleteRequest(BaseModel):
    profile_id: int


class AgentMessage(BaseModel):
    agent_name: str
    display_name: str
    message: str
    accent_color: str


class CompleteResponse(BaseModel):
    messages: list[AgentMessage]


class StatusResponse(BaseModel):
    onboarding_layer: int
    topics_completed: list[str]
    is_complete: bool


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _get_profile_or_404(db: Session, profile_id: int) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


def _profile_to_dict(profile: UserProfile) -> dict:
    """Serialise the relevant profile columns into a plain dict for the AI."""
    return {
        "name": profile.name,
        "location": profile.location,
        "work_status": profile.work_status,
        "study_status": profile.study_status,
        "training_frequency": profile.training_frequency,
        "training_type": profile.training_type,
        "training_experience": profile.training_experience,
        "skin_type": profile.skin_type,
        "skin_concerns": profile.skin_concerns,
        "current_routine_brief": profile.current_routine_brief,
        "active_medications": profile.active_medications,
        "stress_baseline": profile.stress_baseline,
        "anxiety_baseline": profile.anxiety_baseline,
        "sleep_baseline": profile.sleep_baseline,
        "energy_baseline": profile.energy_baseline,
        "supplements": profile.supplements,
        "cycle_length": profile.cycle_length,
        "cycle_tracking": profile.cycle_tracking,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/start", response_model=StartResponse)
def start_onboarding(db: Session = Depends(get_db)):
    profile = UserProfile(name="Shay")
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return StartResponse(profile_id=profile.id, welcome_message=WELCOME_MESSAGE)


@router.post("/extract", response_model=ExtractResponse)
def extract_data(body: ExtractRequest, db: Session = Depends(get_db)):
    if body.topic not in ALL_TOPICS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid topic '{body.topic}'. Must be one of: {', '.join(sorted(ALL_TOPICS))}",
        )

    is_goal_topic = body.topic in GOAL_TOPICS

    if is_goal_topic:
        system_prompt = GOAL_EXTRACTION_PROMPT
    else:
        system_prompt = EXTRACTION_PROMPTS[body.topic]

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": body.raw_input}],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Claude API error: {exc}"
        ) from exc

    raw_text = response.content[0].text

    try:
        extracted = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse Claude response as JSON: {exc}",
        ) from exc

    return ExtractResponse(extracted_data=extracted)


@router.post("/confirm-topic", response_model=ConfirmTopicResponse)
def confirm_topic(body: ConfirmTopicRequest, db: Session = Depends(get_db)):
    if body.topic not in ALL_TOPICS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid topic '{body.topic}'. Must be one of: {', '.join(sorted(ALL_TOPICS))}",
        )

    # We need at least one profile to exist — grab the latest one.
    profile = db.query(UserProfile).order_by(UserProfile.id.desc()).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    is_goal_topic = body.topic in GOAL_TOPICS

    # --- Profile data topics -------------------------------------------------
    if not is_goal_topic:
        allowed_fields = TOPIC_PROFILE_FIELDS.get(body.topic, [])
        for field, value in body.extracted_data.items():
            if field in allowed_fields and hasattr(profile, field):
                setattr(profile, field, value)

    # --- Goal topics ----------------------------------------------------------
    if is_goal_topic and body.goals:
        default_domain = GOAL_TOPIC_DOMAIN_MAP.get(body.topic, "general")
        for goal_data in body.goals:
            goal = Goal(
                title=goal_data.get("title", "Untitled goal"),
                domain=goal_data.get("domain", default_domain),
                goal_type=goal_data.get("goal_type", "north_star"),
                target_value=goal_data.get("target_value"),
                target_unit=goal_data.get("target_unit"),
                deadline=goal_data.get("deadline"),
                linked_agent=goal_data.get("linked_agent", "aurore"),
            )
            db.add(goal)

    # --- Mark topic as completed (idempotent) ---------------------------------
    completed: list[str] = list(profile.topics_completed or [])
    if body.topic not in completed:
        completed.append(body.topic)
    profile.topics_completed = completed

    db.commit()

    return ConfirmTopicResponse(success=True, topic=body.topic)


@router.post("/complete", response_model=CompleteResponse)
def complete_onboarding(body: CompleteRequest, db: Session = Depends(get_db)):
    profile = _get_profile_or_404(db, body.profile_id)

    # Mark profile as onboarded
    profile.onboarding_completed_at = datetime.now(timezone.utc)
    profile.onboarding_layer = 1

    # Create a council round for the introduction messages
    council_round = CouncilRound(
        triggered_by="onboarding",
        agent_order=AGENT_ORDER,
        status="in_progress",
    )
    db.add(council_round)
    db.commit()
    db.refresh(council_round)

    # Build context for agent introductions
    profile_data = _profile_to_dict(profile)
    goals = db.query(Goal).all()
    goals_data = [
        {
            "title": g.title,
            "domain": g.domain,
            "goal_type": g.goal_type,
            "target_value": g.target_value,
            "target_unit": g.target_unit,
            "linked_agent": g.linked_agent,
        }
        for g in goals
    ]

    user_context = json.dumps(
        {"profile": profile_data, "goals": goals_data}, indent=2
    )

    messages_out: list[AgentMessage] = []

    for seq, agent_name in enumerate(AGENT_ORDER):
        agent = get_agent(agent_name)
        system_prompt = get_introduction_prompt(agent)

        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=512,
                system=system_prompt,
                messages=[{"role": "user", "content": user_context}],
            )
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Claude API error for agent {agent_name}: {exc}",
            ) from exc

        text = response.content[0].text

        council_msg = CouncilMessage(
            round_id=council_round.id,
            agent_name=agent_name,
            sequence_order=seq,
            message=text,
            visibility="user_facing",
        )
        db.add(council_msg)

        messages_out.append(
            AgentMessage(
                agent_name=agent_name,
                display_name=agent.display_name,
                message=text,
                accent_color=agent.accent_color,
            )
        )

    # Mark round as complete
    council_round.status = "complete"
    council_round.completed_at = datetime.now(timezone.utc)
    db.commit()

    return CompleteResponse(messages=messages_out)


@router.get("/status", response_model=StatusResponse)
def onboarding_status(profile_id: int, db: Session = Depends(get_db)):
    profile = _get_profile_or_404(db, profile_id)
    return StatusResponse(
        onboarding_layer=profile.onboarding_layer or 0,
        topics_completed=list(profile.topics_completed or []),
        is_complete=profile.onboarding_completed_at is not None,
    )
