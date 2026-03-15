from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import UserProfile

router = APIRouter(prefix="/profile", tags=["profile"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    height_cm: Optional[float] = None
    current_weight_kg: Optional[float] = None
    dob: Optional[date] = None
    location: Optional[str] = None
    work_status: Optional[str] = None
    study_status: Optional[str] = None
    training_frequency: Optional[int] = None
    training_type: Optional[str] = None
    training_experience: Optional[str] = None
    skin_type: Optional[str] = None
    skin_concerns: Optional[list] = None
    current_routine_brief: Optional[str] = None
    active_medications: Optional[list] = None
    stress_baseline: Optional[int] = None
    anxiety_baseline: Optional[int] = None
    sleep_baseline: Optional[int] = None
    energy_baseline: Optional[int] = None
    cycle_length: Optional[int] = None
    cycle_tracking: Optional[bool] = None
    supplements: Optional[list] = None
    onboarding_completed_at: Optional[datetime] = None
    onboarding_layer: Optional[int] = None
    topics_completed: Optional[list] = None


class ProfileResponse(BaseModel):
    id: int
    name: Optional[str]
    height_cm: Optional[float]
    current_weight_kg: Optional[float]
    dob: Optional[date]
    location: Optional[str]
    work_status: Optional[str]
    study_status: Optional[str]
    training_frequency: Optional[int]
    training_type: Optional[str]
    training_experience: Optional[str]
    skin_type: Optional[str]
    skin_concerns: Optional[list]
    current_routine_brief: Optional[str]
    active_medications: Optional[list]
    stress_baseline: Optional[int]
    anxiety_baseline: Optional[int]
    sleep_baseline: Optional[int]
    energy_baseline: Optional[int]
    cycle_length: Optional[int]
    cycle_tracking: Optional[bool]
    supplements: Optional[list]
    onboarding_completed_at: Optional[datetime]
    onboarding_layer: Optional[int]
    topics_completed: Optional[list]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=ProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("", response_model=ProfileResponse)
def update_profile(body: ProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
