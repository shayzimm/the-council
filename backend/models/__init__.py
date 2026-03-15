from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    Boolean,
    Date,
    DateTime,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), default="Shay")
    height_cm = Column(Float, nullable=True)
    current_weight_kg = Column(Float, nullable=True)
    dob = Column(Date, nullable=True)
    location = Column(String(100), nullable=True)
    work_status = Column(String(20), nullable=True)
    study_status = Column(String(20), nullable=True)
    training_frequency = Column(Integer, nullable=True)
    training_type = Column(String(100), nullable=True)
    training_experience = Column(String(20), nullable=True)
    skin_type = Column(String(20), nullable=True)
    skin_concerns = Column(JSON, nullable=True)
    current_routine_brief = Column(Text, nullable=True)
    active_medications = Column(JSON, nullable=True)
    stress_baseline = Column(Integer, nullable=True)
    anxiety_baseline = Column(Integer, nullable=True)
    sleep_baseline = Column(Integer, nullable=True)
    energy_baseline = Column(Integer, nullable=True)
    cycle_length = Column(Integer, nullable=True)
    cycle_tracking = Column(Boolean, default=False)
    supplements = Column(JSON, nullable=True)
    onboarding_completed_at = Column(DateTime, nullable=True)
    onboarding_layer = Column(Integer, default=0)
    topics_completed = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_type = Column(String(20), nullable=False)
    parent_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    domain = Column(String(20), nullable=False)
    linked_agent = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    target_value = Column(Float, nullable=True)
    target_unit = Column(String(20), nullable=True)
    current_value = Column(Float, nullable=True)
    deadline = Column(Date, nullable=True)
    status = Column(String(20), default="active")
    priority = Column(String(20), default="active")
    achieved_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    parent = relationship("Goal", remote_side=[id], backref="children")


class CouncilRound(Base):
    __tablename__ = "council_rounds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    triggered_by = Column(String(30), nullable=False)
    trigger_reference_id = Column(Integer, nullable=True)
    triage_summary = Column(Text, nullable=True)
    agent_order = Column(JSON, nullable=True)
    status = Column(String(20), default="in_progress")
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    messages = relationship("CouncilMessage", back_populates="round")


class CouncilMessage(Base):
    __tablename__ = "council_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    round_id = Column(Integer, ForeignKey("council_rounds.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    internal_reasoning = Column(Text, nullable=True)
    mentions = Column(JSON, nullable=True)
    in_reply_to = Column(Integer, ForeignKey("council_messages.id"), nullable=True)
    visibility = Column(String(20), default="user_facing")
    created_at = Column(DateTime, server_default=func.now())

    round = relationship("CouncilRound", back_populates="messages")
    reply_parent = relationship("CouncilMessage", remote_side=[id], backref="replies")
