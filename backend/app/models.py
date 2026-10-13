from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    String,
    ForeignKey,
    DateTime,
    Float,
    Integer,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc)


class Clinic(Base):
    __tablename__ = "clinics"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(100))


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    clinic_id: Mapped[str] = mapped_column(ForeignKey("clinics.id"), index=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(20))


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    csrf: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    clinic_id: Mapped[str] = mapped_column(ForeignKey("clinics.id"), index=True)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(100))
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(254))
    allergies: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(String(2000), default="")
    status: Mapped[str] = mapped_column(String(20), default="active")
    invite_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True
    )
    invite_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Food(Base):
    __tablename__ = "foods"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    unit: Mapped[float] = mapped_column(Float)
    nutrition: Mapped[dict] = mapped_column(JSON)
    properties: Mapped[dict] = mapped_column(JSON)
    rasas: Mapped[list] = mapped_column(JSON)
    dosha_impact: Mapped[dict] = mapped_column(JSON)
    allergens: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(
        String(200), default="Original hackathon demo; unverified educational data"
    )


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    answers: Mapped[list] = mapped_column(JSON)
    scores: Mapped[dict] = mapped_column(JSON)
    result: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (UniqueConstraint("patient_id", "version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    author_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    title: Mapped[str] = mapped_column(String(120))
    notes: Mapped[str] = mapped_column(String(2000), default="")
    items: Mapped[list] = mapped_column(JSON)
    totals: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class CheckIn(Base):
    __tablename__ = "checkins"
    __table_args__ = (UniqueConstraint("patient_id", "day"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    day: Mapped[str] = mapped_column(String(10))
    adherence: Mapped[int] = mapped_column(Integer)
    energy: Mapped[int] = mapped_column(Integer)
    note: Mapped[str] = mapped_column(String(1000), default="")


class Audit(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    clinic_id: Mapped[str] = mapped_column(ForeignKey("clinics.id"), index=True)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(60))
    resource_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
