from decimal import Decimal

from app.core.metrics.insights import (
    MIN_SEGMENT_N,
    SegmentStat,
    build_insights,
)


def _classify(key, value):
    # minimal stub mirroring default bands enough for assertions
    if value is None:
        return None
    if key == "roi":
        if value < 0:
            return "Perdedor"
        if value < 10:
            return "Regular"
        if value < 30:
            return "Bom"
        return "Excelente"
    return None


def _build(**over):
    base = dict(
        tournaments=200,
        roi_pct=Decimal("15"),
        itm_pct=Decimal("18"),
        total_profit_base=Decimal("1000"),
        total_prize_base=Decimal("800"),
        total_bounty_base=Decimal("200"),
        max_drawdown_base=Decimal("300"),
        longest_loss_streak=12,
        segments={},
        classify=_classify,
        reliability_label="Baixa",
    )
    base.update(over)
    return build_insights(**base)


def test_no_data_returns_single_insight():
    out = build_insights(
        tournaments=0,
        roi_pct=None,
        itm_pct=None,
        total_profit_base=Decimal("0"),
        total_prize_base=Decimal("0"),
        total_bounty_base=Decimal("0"),
        max_drawdown_base=Decimal("0"),
        longest_loss_streak=0,
        segments={},
        classify=_classify,
        reliability_label=None,
    )
    assert len(out) == 1
    assert out[0].id == "no_data"


def test_low_confidence_volume_warning():
    out = _build(tournaments=40, reliability_label="Muito Baixa")
    vol = next(i for i in out if i.id == "volume")
    assert vol.severity == "warning"
    roi = next(i for i in out if i.id == "overall_roi")
    assert "Confiabilidade baixa" in roi.detail


def test_high_volume_no_low_confidence_caveat():
    out = _build(tournaments=1500, reliability_label="Alta")
    roi = next(i for i in out if i.id == "overall_roi")
    assert "Confiabilidade baixa" not in roi.detail


def test_segment_below_threshold_is_not_ranked():
    # two segments, both under MIN_SEGMENT_N -> no best/worst, gets "insufficient"
    segs = {
        "buy_in": [
            SegmentStat("$5", MIN_SEGMENT_N - 1, Decimal("50"), Decimal("40")),
            SegmentStat("$10", 5, Decimal("-20"), Decimal("-15")),
        ]
    }
    out = _build(segments=segs)
    ids = {i.id for i in out}
    assert "segment_buy_in_insufficient" in ids
    assert "segment_buy_in_best" not in ids


def test_segment_ranking_and_leak_detection():
    segs = {
        "buy_in": [
            SegmentStat("$5", 60, Decimal("600"), Decimal("40")),
            SegmentStat("$22", 80, Decimal("-400"), Decimal("-25")),
            SegmentStat("$11", 50, Decimal("100"), Decimal("5")),
        ]
    }
    out = _build(segments=segs)
    best = next(i for i in out if i.id == "segment_buy_in_best")
    worst = next(i for i in out if i.id == "segment_buy_in_worst")
    assert "$5" in best.title
    assert "$22" in worst.title
    assert worst.severity == "negative"


def test_bounty_share_composition():
    out = _build(total_prize_base=Decimal("750"), total_bounty_base=Decimal("250"))
    b = next(i for i in out if i.id == "bounty_share")
    assert "25.0%" in b.title
