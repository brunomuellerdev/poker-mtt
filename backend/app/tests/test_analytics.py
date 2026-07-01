from fastapi.testclient import TestClient

REG = {"name": "An", "email": "an@example.com", "password": "supersecret1"}

BASE = {
    "poker_room": "Stars",
    "game_type": "holdem",
    "betting_structure": "nl",
    "entrants": 500,
    "final_position": 50,
}


def _auth(client: TestClient) -> dict[str, str]:
    client.post("/api/v1/auth/register", json=REG)
    tok = client.post(
        "/api/v1/auth/login", json={"email": REG["email"], "password": REG["password"]}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _mk(client, h, **over):
    return client.post("/api/v1/tournaments", json={**BASE, **over}, headers=h)


def test_breakdown_by_room_roi(client: TestClient):
    h = _auth(client)
    _mk(client, h, poker_room="Stars", buy_in="10", prize="30", date="2024-01-01")  # +20
    _mk(client, h, poker_room="Stars", buy_in="10", prize="0", date="2024-01-02")   # -10
    _mk(client, h, poker_room="GG", buy_in="10", prize="100", date="2024-01-03")    # +90
    rows = client.get("/api/v1/analytics/breakdown?by=room", headers=h).json()
    by_key = {r["key"]: r for r in rows}
    assert by_key["Stars"]["tournaments"] == 2
    assert by_key["Stars"]["profit_base"] == "10.00"
    assert by_key["Stars"]["roi_pct"] == "50.00"     # 10/20
    assert by_key["GG"]["roi_pct"] == "900.00"       # 90/10


def test_breakdown_invalid_dimension_400(client: TestClient):
    h = _auth(client)
    assert client.get("/api/v1/analytics/breakdown?by=nonsense", headers=h).status_code == 400


def test_breakdown_by_weekday(client: TestClient):
    h = _auth(client)
    # 2024-01-01 is a Monday (isodow=1)
    _mk(client, h, date="2024-01-01", buy_in="10", prize="20")
    rows = client.get("/api/v1/analytics/breakdown?by=weekday", headers=h).json()
    assert rows[0]["key"] == "1"  # Monday


def test_monthly_timeseries(client: TestClient):
    h = _auth(client)
    _mk(client, h, date="2024-01-10", buy_in="10", prize="30")
    _mk(client, h, date="2024-01-20", buy_in="10", prize="0")
    _mk(client, h, date="2024-02-05", buy_in="10", prize="50")
    rows = client.get("/api/v1/analytics/timeseries/monthly", headers=h).json()
    months = {r["period"]: r for r in rows}
    assert months["2024-01"]["profit_base"] == "10.00"   # 20 - 10
    assert months["2024-02"]["profit_base"] == "40.00"   # 50 - 10


def test_cumulative_matches_engine_summary(client: TestClient):
    """SQL window-function cumulative must agree with the engine's final total."""
    h = _auth(client)
    _mk(client, h, date="2024-03-01", buy_in="0", prize="100")  # +100
    _mk(client, h, date="2024-03-02", buy_in="40", prize="0")   # -40
    _mk(client, h, date="2024-03-03", buy_in="30", prize="0")   # -30
    cum = client.get("/api/v1/analytics/timeseries/cumulative", headers=h).json()
    assert [c["cumulative_base"] for c in cum] == ["100.00", "60.00", "30.00"]
    # last cumulative == engine total_profit
    summary = client.get("/api/v1/tournaments/summary", headers=h).json()
    assert cum[-1]["cumulative_base"] == summary["total_profit_base"]


def test_indicators_classified_against_user_bands(client: TestClient):
    h = _auth(client)
    # one +200% ROI tournament -> ROI band "Excelente" (>30)
    _mk(client, h, buy_in="10", prize="30", date="2024-04-01")  # roi 200%
    rows = client.get("/api/v1/analytics/indicators", headers=h).json()
    by_ind = {r["indicator"]: r for r in rows}
    assert by_ind["roi"]["classification"] == "Excelente"
    # reliability with 1 tournament -> "Muito Baixa"
    assert by_ind["reliability"]["value"] == "1"
    assert by_ind["reliability"]["classification"] == "Muito Baixa"


def test_analytics_multi_tenant(client: TestClient):
    h = _auth(client)
    _mk(client, h, buy_in="10", prize="30")
    # second user sees nothing
    client.post(
        "/api/v1/auth/register",
        json={"name": "Z", "email": "z@example.com", "password": "supersecret1"},
    )
    tok = client.post(
        "/api/v1/auth/login", json={"email": "z@example.com", "password": "supersecret1"}
    ).json()["access_token"]
    hz = {"Authorization": f"Bearer {tok}"}
    assert client.get("/api/v1/analytics/breakdown?by=room", headers=hz).json() == []
