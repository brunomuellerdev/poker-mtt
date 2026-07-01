
from fastapi.testclient import TestClient

REG = {"name": "A", "email": "a@example.com", "password": "supersecret1"}
REG2 = {"name": "B", "email": "b@example.com", "password": "supersecret1"}

BASE_TOUR = {
    "date": "2024-01-15",
    "poker_room": "Stars",
    "game_type": "holdem",
    "betting_structure": "nl",
    "buy_in": "10.00",
    "entrants": 500,
    "final_position": 50,
}


def _auth(client: TestClient, reg: dict) -> dict[str, str]:
    client.post("/api/v1/auth/register", json=reg)
    token = client.post(
        "/api/v1/auth/login", json={"email": reg["email"], "password": reg["password"]}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create(client: TestClient, headers: dict, **over) -> dict:
    payload = {**BASE_TOUR, **over}
    r = client.post("/api/v1/tournaments", json=payload, headers=headers)
    return r


def test_create_sets_computed_and_final_table_size_from_table_size(client: TestClient):
    h = _auth(client, REG)
    r = _create(
        client, h, table_size=6, buy_in="10", rebuys=2, reentries=1,
        addon_cost="5", prize="100", final_position=3,
    )
    assert r.status_code == 201
    body = r.json()
    # final_table_size defaulted from table_size (6), so position 3 -> final table
    assert body["final_table_size"] == 6
    assert body["final_table"] is True
    # rebuy cost correctness surfaced through the API
    assert body["total_cost"] == "45.00"
    assert body["profit_native"] == "55.00"
    assert body["itm"] is True


def test_explicit_final_table_size_respected(client: TestClient):
    h = _auth(client, REG)
    body = _create(client, h, table_size=9, final_table_size=8, final_position=9).json()
    assert body["final_table_size"] == 8
    assert body["final_table"] is False  # pos 9 > 8


def test_list_requires_auth(client: TestClient):
    assert client.get("/api/v1/tournaments").status_code == 401


def test_multi_tenant_isolation(client: TestClient):
    ha = _auth(client, REG)
    hb = _auth(client, REG2)
    created = _create(client, ha).json()
    tid = created["id"]

    # B cannot read A's tournament
    assert client.get(f"/api/v1/tournaments/{tid}", headers=hb).status_code == 404
    # B's list is empty
    assert client.get("/api/v1/tournaments", headers=hb).json()["items"] == []
    # A sees it
    assert client.get(f"/api/v1/tournaments/{tid}", headers=ha).status_code == 200


def test_offset_pagination_no_overlap(client: TestClient):
    h = _auth(client, REG)
    # 5 tournaments across distinct dates
    for i in range(5):
        _create(client, h, date=f"2024-02-0{i+1}")
    first = client.get("/api/v1/tournaments?limit=2", headers=h).json()
    assert len(first["items"]) == 2
    assert first["has_more"] is True
    assert first["next_offset"] == 2

    second = client.get(
        f"/api/v1/tournaments?limit=2&offset={first['next_offset']}", headers=h
    ).json()
    assert len(second["items"]) == 2

    ids_first = {t["id"] for t in first["items"]}
    ids_second = {t["id"] for t in second["items"]}
    assert ids_first.isdisjoint(ids_second)  # no overlap between pages

    # newest first: page 1 dates are all >= page 2 dates
    assert first["items"][0]["date"] == "2024-02-05"
    assert first["items"][1]["date"] == "2024-02-04"
    assert second["items"][0]["date"] == "2024-02-03"


def test_ordering_date_time_then_created_at(client: TestClient):
    h = _auth(client, REG)
    # same date, different start_time -> later time on top
    _create(client, h, date="2024-05-01", start_time="18:00:00")
    _create(client, h, date="2024-05-01", start_time="21:00:00")
    # later date wins regardless of time
    _create(client, h, date="2024-05-02", start_time="09:00:00")
    items = client.get("/api/v1/tournaments", headers=h).json()["items"]
    assert items[0]["date"] == "2024-05-02"
    assert items[1]["start_time"] == "21:00:00"  # same-day, later time first
    assert items[2]["start_time"] == "18:00:00"


def test_filter_by_buy_in_range(client: TestClient):
    h = _auth(client, REG)
    _create(client, h, buy_in="5", date="2024-03-01")
    _create(client, h, buy_in="50", date="2024-03-02")
    _create(client, h, buy_in="500", date="2024-03-03")
    r = client.get(
        "/api/v1/tournaments?buy_in_min=10&buy_in_max=100", headers=h
    ).json()
    assert len(r["items"]) == 1
    assert r["items"][0]["buy_in"] == "50.00"


def test_created_at_tiebreaker_same_date_no_time(client: TestClient):
    h = _auth(client, REG)
    # same date, no start_time -> the later-created one is on top
    a = _create(client, h, date="2024-06-01", tournament_name="A").json()
    b = _create(client, h, date="2024-06-01", tournament_name="B").json()
    items = client.get("/api/v1/tournaments", headers=h).json()["items"]
    assert items[0]["id"] == b["id"]  # created last -> top
    assert items[1]["id"] == a["id"]


def test_update_and_delete(client: TestClient):
    h = _auth(client, REG)
    tid = _create(client, h).json()["id"]
    # update prize -> recomputed itm
    up = client.patch(
        f"/api/v1/tournaments/{tid}", json={"prize": "200.00"}, headers=h
    ).json()
    assert up["prize"] == "200.00"
    assert up["itm"] is True
    # delete
    assert client.delete(f"/api/v1/tournaments/{tid}", headers=h).status_code == 204
    assert client.get(f"/api/v1/tournaments/{tid}", headers=h).status_code == 404


def test_attach_tags_and_reject_foreign_tag(client: TestClient):
    ha = _auth(client, REG)
    hb = _auth(client, REG2)
    tag_a = client.post("/api/v1/tags", json={"name": "leak"}, headers=ha).json()["id"]
    tag_b = client.post("/api/v1/tags", json={"name": "bovada"}, headers=hb).json()["id"]

    # A attaches own tag -> ok
    ok = _create(client, ha, tag_ids=[tag_a])
    assert ok.status_code == 201
    assert [t["name"] for t in ok.json()["tags"]] == ["leak"]

    # A attaches B's tag -> 422 (cross-tenant tag rejected)
    bad = _create(client, ha, tag_ids=[tag_b])
    assert bad.status_code == 422


def test_summary_matches_engine(client: TestClient):
    h = _auth(client, REG)
    _create(client, h, buy_in="10", prize="30", date="2024-04-01")  # +20
    _create(client, h, buy_in="10", prize="0", date="2024-04-02")   # -10
    s = client.get("/api/v1/tournaments/summary", headers=h).json()
    assert s["tournaments"] == 2
    assert s["total_profit_base"] == "10.00"   # 20 - 10
    assert s["roi_pct"] == "50.00"             # 10 / 20 * 100


def test_tag_duplicate_conflict(client: TestClient):
    h = _auth(client, REG)
    assert client.post("/api/v1/tags", json={"name": "dup"}, headers=h).status_code == 201
    assert client.post("/api/v1/tags", json={"name": "dup"}, headers=h).status_code == 409


def test_bounty_only_tournament_persists_and_not_itm(client: TestClient):
    h = _auth(client, REG)
    body = _create(
        client, h, buy_in="20", prize="0", bounty="35",
        allows_reentry=True, final_position=120,
    ).json()
    assert body["bounty"] == "35.00"          # bounty persisted through the API
    assert body["total_winnings"] == "35.00"
    assert body["profit_base"] == "15.00"     # 35 - 20
    assert body["itm"] is False               # no position prize


def test_tournament_type_and_flags_combine(client: TestClient):
    h = _auth(client, REG)
    # satellite that also allows rebuy AND reentry — the case that was impossible before
    body = _create(
        client, h, tournament_type="satellite",
        allows_rebuy=True, allows_reentry=True, allows_addon=False,
    ).json()
    assert body["tournament_type"] == "satellite"
    assert body["allows_rebuy"] is True
    assert body["allows_reentry"] is True
    assert body["allows_addon"] is False


def test_breakdown_by_tournament_type(client: TestClient):
    h = _auth(client, REG)
    _create(client, h, tournament_type="normal", buy_in="10", prize="30")
    _create(client, h, tournament_type="satellite", buy_in="10", prize="0")
    rows = client.get("/api/v1/analytics/breakdown?by=tournament_type", headers=h).json()
    keys = {r["key"] for r in rows}
    assert keys == {"normal", "satellite"}
