from .conftest import register, patient, plan


def test_timestamps_include_timezone(client):
    register(client)
    pid = patient(client)
    assert (
        client.get("/api/patients/" + pid)
        .json()["created_at"]
        .endswith(("Z", "+00:00"))
    )
    assert plan(client, pid).json()["created_at"].endswith(("Z", "+00:00"))
