from pathlib import Path

from app.core.hands import hand_to_dict, parse_hands

FIX = Path(__file__).parent / "fixtures" / "hands"


def _file(substr: str) -> str:
    f = next(p for p in FIX.glob("*.txt") if substr in p.name)
    return f.read_text(encoding="utf-8")


def test_all_fixture_hands_parse_and_serialize():
    total = 0
    for f in FIX.glob("*.txt"):
        hands = parse_hands(f.read_text(encoding="utf-8"))
        for h in hands:
            assert h.frames, f"no frames for {h.hand_id}"
            hand_to_dict(h)  # serializable
            total += 1
    assert total > 100  # ~145 across the fixtures


def test_side_pot_hand_totals_and_winner():
    hands = {h.hand_id: h for h in parse_hands(_file("4010772241"))}
    h = hands["261297362381"]
    assert h.variant == "tournament"
    assert h.is_chips is True
    assert h.board == ["2d", "6s", "9d", "5s", "8d"]
    # computed running pot equals the summary total pot
    assert h.frames[-1].pot == h.total_pot == __import__("decimal").Decimal("13515")
    winners = {p["name"]: p["won"] for p in h.frames[-1].players if p["won"] != "0"}
    assert winners == {"JoaquinOmito": "13515"}
    hero = next(p for p in h.frames[-1].players if p["is_hero"])
    assert hero["name"] == "Timefalls"
    assert hero["cards"] == ["Kh", "Kc"]
    assert hand_to_dict(h)["hero_cards"] == ["Kh", "Kc"]
    assert hero["all_in"] is True


def test_cash_hand_detected():
    h = parse_hands(_file("Sicilia"))[0]
    assert h.variant == "cash"
    assert h.currency == "$"
    assert h.tournament_id is None
    assert (h.small_blind, h.big_blind) == (
        __import__("decimal").Decimal("0.05"),
        __import__("decimal").Decimal("0.10"),
    )


def test_pko_bounty_parsed():
    h = parse_hands(_file("4010773551"))[0]
    assert h.buyin == "$2.45+$2.45+$0.60"
    hero = next(p for p in h.frames[-1].players if p["is_hero"])
    assert hero["bounty"] == "2.45"


def test_special_char_player_names():
    # "$$tr8 Hemp" — spaces and $ in name must not break action parsing
    hands = parse_hands(_file("4010772208"))
    names = set()
    for h in hands:
        for p in h.frames[-1].players:
            names.add(p["name"])
    assert "$$tr8 Hemp" in names


def test_uncalled_bet_returned_restores_stack():
    # 3-max all-in hand: Timefalls busts 3rd
    h = parse_hands(_file("4012517499"))[0]
    assert h.hero == "Timefalls"
    # winner Yllinhooo collected the pot
    winners = {p["name"]: p["won"] for p in h.frames[-1].players if p["won"] != "0"}
    assert "Yllinhooo" in winners


def test_empty_text_returns_no_hands():
    assert parse_hands("") == []
    assert parse_hands("garbage line\nanother") == []
