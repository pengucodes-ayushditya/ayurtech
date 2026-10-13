import os
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema, DropSchema
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base, get_db
from app.main import app, login_attempts
from app.models import Food

BACKENDS = ["sqlite"]
if os.getenv("TEST_DATABASES") == "both":
    url = make_url(os.environ["DATABASE_URL"])
    if url.get_backend_name() != "postgresql" or not (url.database or "").endswith(
        "_test"
    ):
        raise RuntimeError("PostgreSQL fixture requires an isolated *_test database")
    BACKENDS.append("postgres")


@pytest.fixture(params=BACKENDS)
def client(request):
    schema = None
    if request.param == "postgres":
        root_engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
        schema = "test_" + uuid4().hex
        with root_engine.begin() as connection:
            connection.execute(CreateSchema(schema))
        engine = root_engine.execution_options(schema_translate_map={None: schema})
    else:
        root_engine = engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
    Base.metadata.create_all(engine)
    maker = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        with maker() as db:
            yield db

    app.dependency_overrides[get_db] = override
    login_attempts.clear()
    with maker() as db:
        db.add_all(
            [
                Food(
                    id="rice",
                    name="Rice",
                    unit=100,
                    nutrition={
                        "calories": 130,
                        "protein": 2.7,
                        "carbs": 28,
                        "fat": 0.3,
                    },
                    properties={"thermal": "Cold", "digestibility": "Easy"},
                    rasas=["Sweet"],
                    dosha_impact={},
                    allergens=[],
                ),
                Food(
                    id="milk",
                    name="Milk",
                    unit=100,
                    nutrition={
                        "calories": 61,
                        "protein": 3.2,
                        "carbs": 4.8,
                        "fat": 3.3,
                    },
                    properties={},
                    rasas=[],
                    dosha_impact={},
                    allergens=["milk"],
                ),
            ]
        )
        db.commit()
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()
        if schema:
            with root_engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
        root_engine.dispose()


def register(client, email="doctor@example.com"):
    r = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "LongPassword!123",
            "name": "Test Doctor",
            "clinic_name": "Test Clinic",
        },
    )
    assert r.status_code == 201, r.text
    client.headers["X-CSRF-Token"] = r.json()["csrf"]
    return r.json()


def patient(client, email="patient@example.com", allergies=None):
    r = client.post(
        "/api/patients",
        json={
            "name": "Test Patient",
            "age": 30,
            "gender": "Female",
            "email": email,
            "allergies": allergies or [],
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def plan(client, pid, version=0, food="rice", grams=150):
    return client.post(
        f"/api/patients/{pid}/plans",
        json={
            "title": "Test plan",
            "notes": "Sample",
            "expected_version": version,
            "items": [{"meal": "Lunch", "food_id": food, "grams": grams}],
        },
    )
