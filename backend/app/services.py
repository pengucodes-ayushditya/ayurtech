from fastapi import HTTPException
from sqlalchemy import select
from .models import Patient, Food, Audit


def accessible_patient(db, user, patient_id):
    patient = db.get(Patient, patient_id)
    if (
        not patient
        or patient.clinic_id != user.clinic_id
        or (user.role == "patient" and patient.user_id != user.id)
    ):
        raise HTTPException(404, "Patient not found")
    return patient


def audit(db, user, action, resource_id):
    db.add(
        Audit(
            clinic_id=user.clinic_id,
            actor_id=user.id,
            action=action,
            resource_id=resource_id,
        )
    )


def calculate_plan(db, patient, items):
    foods = {
        f.id: f
        for f in db.scalars(select(Food).where(Food.id.in_([i.food_id for i in items])))
    }
    snapshots, totals = [], dict(calories=0.0, protein=0.0, carbs=0.0, fat=0.0)
    for item in items:
        food = foods.get(item.food_id)
        if not food:
            raise HTTPException(422, "Unknown food")
        conflicts = set(patient.allergies) & set(food.allergens)
        if conflicts:
            raise HTTPException(
                422,
                f'{food.name} conflicts with recorded allergens: {", ".join(sorted(conflicts))}',
            )
        nutrients = {
            k: round(food.nutrition[k] * item.grams / food.unit, 2) for k in totals
        }
        for k in totals:
            totals[k] += nutrients[k]
        snapshots.append(
            {
                **item.model_dump(),
                "name": food.name,
                "nutrition": nutrients,
                "rasas": food.rasas,
                "properties": food.properties,
                "dosha_impact": food.dosha_impact,
            }
        )
    return snapshots, {k: round(v, 2) for k, v in totals.items()}
