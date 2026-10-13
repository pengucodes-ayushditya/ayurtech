"""Explicit demo seeding. Do not create demo accounts in production."""

import json, os
from pathlib import Path
from sqlalchemy import select
from .db import SessionLocal
from .models import Clinic, User, Patient, Food, Plan, Assessment
from .security import hash_password
from .services import calculate_plan
from .schemas import MealIn


def seed(demo=False):
    if demo and os.getenv("APP_ENV") == "production":
        raise RuntimeError("Demo accounts forbidden in production")
    with SessionLocal() as db:
        if not db.scalar(select(Food.id).limit(1)):
            for row in json.loads(Path(__file__).with_name("foods.json").read_text()):
                db.add(Food(**row))
            db.commit()
        if not demo or db.scalar(
            select(User).where(User.email == "dietitian@ayurtech.demo")
        ):
            return
        clinic = Clinic(name="AyurTech Demo Practice")
        db.add(clinic)
        db.flush()
        doctor = User(
            clinic_id=clinic.id,
            name="Dr. Ananya Sharma",
            email="dietitian@ayurtech.demo",
            password_hash=hash_password("AyurTechDemo!2026"),
            role="dietitian",
        )
        user = User(
            clinic_id=clinic.id,
            name="Priya Singh",
            email="patient@ayurtech.demo",
            password_hash=hash_password("AyurTechDemo!2026"),
            role="patient",
        )
        db.add_all([doctor, user])
        db.flush()
        names = [
            ("Priya Singh", 29, "Female", "patient@ayurtech.demo", "Vata"),
            ("Rohan Verma", 45, "Male", "rohan@example.com", "Pitta-Kapha"),
            ("Aanya Gupta", 35, "Female", "aanya@example.com", "Vata-Pitta"),
            ("Amit Patel", 52, "Male", "amit@example.com", "Kapha"),
            ("Vikram Rao", 42, "Male", "vikram@example.com", "Pitta"),
        ]
        for i, (name, age, gender, email, dosha) in enumerate(names):
            p = Patient(
                clinic_id=clinic.id,
                user_id=user.id if i == 0 else None,
                name=name,
                age=age,
                gender=gender,
                email=email,
                allergies=["milk"] if i == 2 else [],
                notes="Fictional demo profile. Prefers home-cooked meals.",
            )
            db.add(p)
            db.flush()
            if i < 4:
                scores = (
                    {"Vata": 6, "Pitta": 0, "Kapha": 0}
                    if dosha == "Vata"
                    else (
                        {"Vata": 0, "Pitta": 0, "Kapha": 6}
                        if dosha == "Kapha"
                        else {
                            "Vata": 3 if "Vata" in dosha else 0,
                            "Pitta": 3,
                            "Kapha": 3 if "Kapha" in dosha else 0,
                        }
                    )
                )
                answers = [k for k, v in scores.items() for _ in range(v)]
                db.add(
                    Assessment(
                        patient_id=p.id,
                        kind="prakriti",
                        answers=answers,
                        scores=scores,
                        result=dosha,
                    )
                )
            if i < 2:
                items = [
                    MealIn(meal="Breakfast", food_id="8", grams=180),
                    MealIn(meal="Mid-morning", food_id="14", grams=100),
                    MealIn(meal="Lunch", food_id="2", grams=200),
                    MealIn(meal="Lunch", food_id="1", grams=200),
                    MealIn(meal="Evening snack", food_id="6", grams=20),
                    MealIn(meal="Dinner", food_id="9", grams=200),
                    MealIn(meal="Dinner", food_id="21", grams=150),
                ]
                snapshots, totals = calculate_plan(db, p, items)
                db.add(
                    Plan(
                        patient_id=p.id,
                        author_id=doctor.id,
                        version=1,
                        status="published",
                        title="A balanced everyday rhythm",
                        notes="Fictional example for demonstrating the planning workflow, not a dietary prescription.",
                        items=snapshots,
                        totals=totals,
                    )
                )
        db.commit()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    seed(args.demo)
