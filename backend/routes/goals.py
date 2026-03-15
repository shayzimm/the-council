from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Goal

router = APIRouter(prefix="/goals", tags=["goals"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class GoalCreate(BaseModel):
    goal_type: str
    domain: str
    linked_agent: str
    title: str
    description: Optional[str] = None
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    deadline: Optional[date] = None
    priority: Optional[str] = "active"
    parent_id: Optional[int] = None


class GoalUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    current_value: Optional[float] = None
    notes: Optional[str] = None
    deadline: Optional[date] = None
    title: Optional[str] = None
    description: Optional[str] = None
    target_value: Optional[float] = None
    target_unit: Optional[str] = None


class GoalResponse(BaseModel):
    id: int
    goal_type: str
    parent_id: Optional[int]
    domain: str
    linked_agent: str
    title: str
    description: Optional[str]
    target_value: Optional[float]
    target_unit: Optional[str]
    current_value: Optional[float]
    deadline: Optional[date]
    status: Optional[str]
    priority: Optional[str]
    achieved_at: Optional[datetime]
    notes: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=list[GoalResponse])
def list_goals(
    status: Optional[str] = None,
    domain: Optional[str] = None,
    priority: Optional[str] = None,
    linked_agent: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Goal)
    if status:
        query = query.filter(Goal.status == status)
    if domain:
        query = query.filter(Goal.domain == domain)
    if priority:
        query = query.filter(Goal.priority == priority)
    if linked_agent:
        query = query.filter(Goal.linked_agent == linked_agent)
    return query.all()


@router.get("/focus", response_model=list[GoalResponse])
def list_focus_goals(db: Session = Depends(get_db)):
    return db.query(Goal).filter(Goal.priority == "focus").all()


@router.post("", response_model=GoalResponse, status_code=201)
def create_goal(body: GoalCreate, db: Session = Depends(get_db)):
    goal = Goal(**body.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(goal_id: int, body: GoalUpdate, db: Session = Depends(get_db)):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(goal, field, value)

    db.commit()
    db.refresh(goal)
    return goal
