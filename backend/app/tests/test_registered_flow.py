from fastapi.testclient import TestClient

REG={"name":"R","email":"regflow@t.com","password":"supersecret1"}
def _auth(client):
    client.post("/api/v1/auth/register", json=REG)
    tok=client.post("/api/v1/auth/login", json={"email":REG["email"],"password":REG["password"]}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}
BASE=dict(date="2026-06-30",poker_room="PokerStars",game_type="holdem",betting_structure="nl",buy_in="10")

def test_registered_flow(client):
    h=_auth(client)
    # 1) registered
    reg=client.post("/api/v1/tournaments", json={**BASE,"status":"registered"}, headers=h)
    assert reg.status_code==201, reg.text
    rj=reg.json()
    assert rj["status"]=="registered"
    assert rj["entrants"] is None and rj["final_position"] is None
    # 2) completed
    comp=client.post("/api/v1/tournaments", json={**BASE,"entrants":100,"final_position":5,"prize":"50"}, headers=h)
    assert comp.status_code==201
    assert comp.json()["status"]=="completed"
    # 3) metrics exclude registered -> only 1 counted (reliability = tournament count)
    def _count(hh):
        ind=client.get("/api/v1/analytics/indicators", headers=hh).json()
        rel=next(i for i in ind if i["indicator"]=="reliability")
        return int(float(rel["value"]))
    assert _count(h)==1
    # 4) list shows both
    lst=client.get("/api/v1/tournaments", headers=h).json()
    assert sorted(i["status"] for i in lst["items"])==["completed","registered"]
    # 5) complete the registered one
    upd=client.patch(f"/api/v1/tournaments/{rj['id']}", json={"status":"completed","entrants":80,"final_position":1,"prize":"200"}, headers=h)
    assert upd.status_code==200, upd.text
    uj=upd.json()
    assert uj["status"]=="completed" and uj["itm"] is True and uj["winner"] is True
    # 6) metrics now count both
    assert _count(h)==2

def test_completed_requires_result(client):
    h=_auth(client)
    r=client.post("/api/v1/tournaments", json={**BASE}, headers=h)  # no entrants/final_position
    assert r.status_code==422, r.text
