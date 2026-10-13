"""Runs only against a migrated, isolated PostgreSQL *_test database in CI."""

import os
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.db import SessionLocal
from app.models import Clinic, User, Patient, Plan, Audit, Assessment, CheckIn, Session
from .conftest import register, patient, plan


@pytest.mark.skipif(
    "postgresql" not in os.getenv("DATABASE_URL", "")
    or "_test" not in os.getenv("DATABASE_URL", ""),
    reason="Requires isolated PostgreSQL test database",
)
def test_postgres_real_database_workflow():
    with TestClient(app) as client:
        register(client, "postgres-test@example.com")
        try:
            pid = patient(client, "postgres-patient@example.com")
            saved = plan(client, pid, food="2").json()
            assert saved["version"] == 1
            assert (
                client.post(
                    f'/api/patients/{pid}/plans/{saved["id"]}/publish'
                ).status_code
                == 200
            )
            assert plan(client, pid, food="2").status_code == 409
            assert (
                client.get("/api/patients/" + pid).json()["plans"][0]["status"]
                == "published"
            )
            # Two stale clients must not create two copies of version 2.
            cookies = dict(client.cookies)
            csrf = client.headers["X-CSRF-Token"]

            def simultaneous_save(_):
                with TestClient(
                    app, cookies=cookies, headers={"X-CSRF-Token": csrf}
                ) as peer:
                    return plan(peer, pid, version=1, food="2").status_code

            with ThreadPoolExecutor(max_workers=2) as pool:
                statuses = list(pool.map(simultaneous_save, range(2)))
            assert sorted(statuses) == [201, 409], statuses
            versions = client.get("/api/patients/" + pid).json()["plans"]
            assert [p["version"] for p in versions] == [2, 1]
            assert versions[1]["totals"]["calories"] == 195
        finally:
            with SessionLocal() as db:
                user = db.scalar(
                    select(User).where(User.email == "postgres-test@example.com")
                )
                if user:
                    ids = select(Patient.id).where(Patient.clinic_id == user.clinic_id)
                    for model in (Plan, Assessment, CheckIn):
                        db.execute(
                            model.__table__.delete().where(model.patient_id.in_(ids))
                        )
                    db.execute(
                        Audit.__table__.delete().where(
                            Audit.clinic_id == user.clinic_id
                        )
                    )
                    db.execute(
                        Patient.__table__.delete().where(
                            Patient.clinic_id == user.clinic_id
                        )
                    )
                    db.execute(
                        Session.__table__.delete().where(Session.user_id == user.id)
                    )
                    cid = user.clinic_id
                    db.delete(user)
                    db.flush()
                    db.delete(db.get(Clinic, cid))
                    db.commit()
