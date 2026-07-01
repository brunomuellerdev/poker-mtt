from pathlib import Path

from fastapi.testclient import TestClient

FIX = Path(__file__).parent / "fixtures" / "hands"
REG = {"name": "R", "email": "replay@t.com", "password": "supersecret1"}


def _auth(client: TestClient) -> dict:
    client.post("/api/v1/auth/register", json=REG)
    tok = client.post(
        "/api/v1/auth/login",
        json={"email": REG["email"], "password": REG["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _upload(client, headers, substr):
    f = next(p for p in FIX.glob("*.txt") if substr in p.name)
    return client.post(
        "/api/v1/hands/parse",
        headers=headers,
        files={"file": (f.name, f.read_bytes(), "text/plain")},
    )


def test_parse_endpoint_returns_frames(client: TestClient):
    h = _auth(client)
    r = _upload(client, h, "4010772241")
    assert r.status_code == 200
    hands = r.json()["hands"]
    assert len(hands) == 9
    first = hands[0]
    assert first["variant"] == "tournament"
    assert first["frames"]
    assert "pot" in first["frames"][0]


def test_parse_requires_auth(client: TestClient):
    f = next(p for p in FIX.glob("*.txt") if "Sicilia" in p.name)
    r = client.post(
        "/api/v1/hands/parse",
        files={"file": (f.name, f.read_bytes(), "text/plain")},
    )
    assert r.status_code in (401, 403)


def test_parse_garbage_422(client: TestClient):
    h = _auth(client)
    r = client.post(
        "/api/v1/hands/parse",
        headers=h,
        files={"file": ("x.txt", b"not a hand history", "text/plain")},
    )
    assert r.status_code == 422
