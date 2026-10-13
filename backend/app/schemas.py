from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class Credentials(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def email_format(cls, v):
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1] or " " in v:
            raise ValueError("Enter a valid email")
        return v


class Register(Credentials):
    name: str = Field(min_length=2, max_length=100)
    clinic_name: str = Field(min_length=2, max_length=100)


class Claim(Credentials):
    token: str = Field(min_length=20, max_length=100)


class PatientIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=18, le=120)
    gender: Literal["Female", "Male", "Other", "Prefer not to say"] = (
        "Prefer not to say"
    )
    email: str = Field(max_length=254)
    allergies: list[str] = Field(default_factory=list, max_length=20)
    notes: str = Field(default="", max_length=2000)
    status: Literal["active", "archived"] = "active"
    _email = field_validator("email")(Credentials.email_format.__func__)

    @field_validator("allergies")
    @classmethod
    def normalized_allergies(cls, v):
        if any(len(a) > 60 for a in v):
            raise ValueError("Allergen name too long")
        return sorted(set(a.strip().lower() for a in v if a.strip()))


class AssessmentIn(BaseModel):
    kind: Literal["prakriti", "vikriti"]
    answers: list[Literal["Vata", "Pitta", "Kapha"]] = Field(min_length=6, max_length=6)


class MealIn(BaseModel):
    meal: Literal["Breakfast", "Mid-morning", "Lunch", "Evening snack", "Dinner"]
    food_id: str
    grams: float = Field(gt=0, le=2000, allow_inf_nan=False)


class PlanIn(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    notes: str = Field(default="", max_length=2000)
    items: list[MealIn] = Field(min_length=1, max_length=60)
    expected_version: int = Field(ge=0)


class CheckInIn(BaseModel):
    day: date
    adherence: int = Field(ge=0, le=100)
    energy: int = Field(ge=1, le=5)
    note: str = Field(default="", max_length=1000)
