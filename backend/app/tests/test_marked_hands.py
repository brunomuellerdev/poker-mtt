from fastapi.testclient import TestClient

REG = {"name": "H", "email": "hands@t.com", "password": "supersecret1"}


def _auth(client: TestClient) -> dict:
    client.post("/api/v1/auth/register", json=REG)
    tok = client.post(
        "/api/v1/auth/login",
        json={"email": REG["email"], "password": REG["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_marked_hand_crud(client: TestClient):
    h = _auth(client)
    created = client.post(
        "/api/v1/marked-hands",
        json={"hand_code": "#261297021889", "poker_room": "GGPoker", "date": "2024-03-10"},
        headers=h,
    )
    assert created.status_code == 201
    hid = created.json()["id"]
    assert created.json()["hand_code"] == "#261297021889"

    lst = client.get("/api/v1/marked-hands", headers=h).json()
    assert len(lst) == 1

    upd = client.patch(
        f"/api/v1/marked-hands/{hid}", json={"poker_room": "PokerStars"}, headers=h
    )
    assert upd.status_code == 200
    assert upd.json()["poker_room"] == "PokerStars"
    assert upd.json()["hand_code"] == "#261297021889"  # unchanged

    assert client.delete(f"/api/v1/marked-hands/{hid}", headers=h).status_code == 204
    assert client.get("/api/v1/marked-hands", headers=h).json() == []


def test_marked_hand_validation_and_isolation(client: TestClient):
    h = _auth(client)
    # empty hand_code rejected
    bad = client.post(
        "/api/v1/marked-hands",
        json={"hand_code": "", "poker_room": "GGPoker", "date": "2024-03-10"},
        headers=h,
    )
    assert bad.status_code == 422
    # another user cannot see/edit
    other = client.post(
        "/api/v1/marked-hands",
        json={"hand_code": "#1", "poker_room": "GGPoker", "date": "2024-03-10"},
        headers=h,
    ).json()
    client.post(
        "/api/v1/auth/register",
        json={"name": "B", "email": "b2@t.com", "password": "supersecret1"},
    )
    tok2 = client.post(
        "/api/v1/auth/login",
        json={"email": "b2@t.com", "password": "supersecret1"},
    ).json()["access_token"]
    h2 = {"Authorization": f"Bearer {tok2}"}
    assert client.get("/api/v1/marked-hands", headers=h2).json() == []
    assert (
        client.patch(
            f"/api/v1/marked-hands/{other['id']}",
            json={"poker_room": "WPT Global"},
            headers=h2,
        ).status_code
        == 404
    )


def test_marked_hand_with_replay_persists_and_serves(client: TestClient):
    h = _auth(client)
    replay = {
        "hand_id": "999",
        "hero_cards": ["Ah", "Kh"],
        "board": ["2c", "7d", "9s"],
        "frames": [{"label": "x", "pot": "0", "players": [], "actor": None}],
    }
    created = client.post(
        "/api/v1/marked-hands",
        json={
            "hand_code": "#999",
            "poker_room": "PokerStars",
            "date": "2026-06-30",
            "replay": replay,
        },
        headers=h,
    ).json()
    assert created["has_replay"] is True
    assert created["hero_cards"] == ["Ah", "Kh"]
    assert created["board"] == ["2c", "7d", "9s"]

    # list stays lightweight (no replay key)
    lst = client.get("/api/v1/marked-hands", headers=h).json()
    assert "replay" not in lst[0]
    assert lst[0]["has_replay"] is True

    # replay endpoint returns the stored frames
    rep = client.get(
        f"/api/v1/marked-hands/{created['id']}/replay", headers=h
    ).json()
    assert rep["replay"]["hero_cards"] == ["Ah", "Kh"]
    assert rep["replay"]["frames"][0]["actor"] is None


def test_manual_marked_hand_has_no_replay(client: TestClient):
    h = _auth(client)
    created = client.post(
        "/api/v1/marked-hands",
        json={"hand_code": "#12", "poker_room": "GGPoker", "date": "2026-06-30"},
        headers=h,
    ).json()
    assert created["has_replay"] is False
    rep = client.get(
        f"/api/v1/marked-hands/{created['id']}/replay", headers=h
    ).json()
    assert rep["replay"] is None
