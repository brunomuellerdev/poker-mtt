import uuid
from datetime import date, time
from decimal import Decimal

from app.core.metrics.classification import Band, classify
from app.core.metrics.engine import (
    TournamentResult,
    chronological,
    cumulative_profit,
    is_itm,
    max_drawdown,
    max_upswing,
    profit_base,
    summarize,
    total_cost_native,
)


def _t(
    *,
    d="2024-01-01",
    st=None,
    buy_in="10",
    rebuys=0,
    reentries=0,
    addon_cost="0",
    prize="0",
    bounty="0",
    fx="1.0",
    pos=100,
    fts=9,
    tid=None,
) -> TournamentResult:
    return TournamentResult(
        id=tid or uuid.uuid4(),
        date=date.fromisoformat(d),
        start_time=time.fromisoformat(st) if st else None,
        buy_in=Decimal(buy_in),
        rebuys=rebuys,
        reentries=reentries,
        addon_cost=Decimal(addon_cost),
        prize=Decimal(prize),
        bounty=Decimal(bounty),
        fx_rate_to_base=Decimal(fx),
        final_position=pos,
        final_table_size=fts,
    )


# --- the canonical correctness fix: rebuy cost ---

def test_rebuy_cost_includes_rebuys_reentries_addon():
    t = _t(buy_in="10", rebuys=2, reentries=1, addon_cost="5", prize="100")
    assert total_cost_native(t) == Decimal("45")
    assert profit_base(t) == Decimal("55")


def test_addon_cost_not_multiplied_by_buyin():
    # add-on priced independently, not as a buy-in multiple
    t = _t(buy_in="10", rebuys=0, reentries=0, addon_cost="3", prize="0")
    assert total_cost_native(t) == Decimal("13")


def test_bounty_counts_toward_profit_but_not_itm():
    # PKO: busted out of the money (prize 0) but won 35 in bounties on a 20 buy-in
    t = _t(buy_in="20", prize="0", bounty="35", pos=120)
    assert profit_base(t) == Decimal("15")   # 35 - 20, bounty makes it profitable
    assert is_itm(t) is False                 # no position prize -> not ITM


def test_bounty_included_in_summary_profit_not_itm_pct():
    results = [
        _t(buy_in="20", prize="0", bounty="50", pos=200),  # bounty only, not ITM
        _t(buy_in="20", prize="60", bounty="10", pos=2),   # ITM + bounty
    ]
    s = summarize(results)
    # cost 40; winnings (0+50)+(60+10)=120; profit 80
    assert s.total_profit_base == Decimal("80")
    assert s.total_bounty_base == Decimal("60")
    assert s.total_prize_base == Decimal("60")
    assert s.itm_pct == Decimal("50")  # only 1 of 2 reached the money


# --- aggregate ROI ---

def test_roi_aggregates_over_summed_cost_and_profit():
    # two $10 freezeouts: one wins 30, one busts (0)
    results = [
        _t(buy_in="10", prize="30"),
        _t(buy_in="10", prize="0"),
    ]
    s = summarize(results)
    # cost 20, prizes 30 -> profit 10 -> ROI 50%
    assert s.total_buyins_base == Decimal("20")
    assert s.total_profit_base == Decimal("10")
    assert s.roi_pct == Decimal("50")


def test_roi_none_when_no_cost():
    assert summarize([]).roi_pct is None


def test_empty_summary_is_safe():
    s = summarize([])
    assert s.tournaments == 0
    assert s.max_drawdown_base == Decimal("0")
    assert s.longest_win_streak == 0


# --- percentages ---

def test_itm_final_table_win_pct():
    results = [
        _t(prize="50", pos=1, fts=9),    # itm, final table, win
        _t(prize="20", pos=5, fts=9),    # itm, final table
        _t(prize="0", pos=200, fts=9),   # nothing
        _t(prize="0", pos=300, fts=9),   # nothing
    ]
    s = summarize(results)
    assert s.win_pct == Decimal("25")            # 1/4
    assert s.final_table_pct == Decimal("50")    # 2/4
    assert s.itm_pct == Decimal("50")            # 2/4


# --- currency conversion in aggregation ---

def test_fx_applied_to_base_aggregation():
    # profit native 90 (100-10) at fx 5.0 -> base 450
    t = _t(buy_in="10", prize="100", fx="5.0")
    s = summarize([t])
    assert s.total_profit_base == Decimal("450")
    assert s.abi_base == Decimal("50")  # buy_in 10 * 5.0


# --- cumulative / drawdown / upswing ---

def test_cumulative_and_drawdown():
    # per-tournament profits: +100, -40, -30, +20  (buy_in 0 to control profit via prize)
    seq = [
        _t(buy_in="0", prize="100", d="2024-01-01", tid=uuid.UUID(int=1)),
        _t(buy_in="40", prize="0", d="2024-01-02", tid=uuid.UUID(int=2)),
        _t(buy_in="30", prize="0", d="2024-01-03", tid=uuid.UUID(int=3)),
        _t(buy_in="0", prize="20", d="2024-01-04", tid=uuid.UUID(int=4)),
    ]
    series = cumulative_profit(seq)
    assert series == [Decimal("100"), Decimal("60"), Decimal("30"), Decimal("50")]
    # peak 100 then down to 30 -> drawdown 70
    assert max_drawdown(series) == Decimal("70")


def test_max_upswing():
    # profits: -50, +120  -> cumulative -50, 70 ; trough -50 -> upswing 120
    seq = [
        _t(buy_in="50", prize="0", d="2024-01-01", tid=uuid.UUID(int=1)),
        _t(buy_in="0", prize="120", d="2024-01-02", tid=uuid.UUID(int=2)),
    ]
    assert max_upswing(cumulative_profit(seq)) == Decimal("120")


# --- streaks ---

def test_streaks_with_breakeven_breaking_both():
    # signs: + + 0 - -  -> longest win 2, longest loss 2
    seq = [
        _t(buy_in="0", prize="5", d="2024-01-01", tid=uuid.UUID(int=1)),
        _t(buy_in="0", prize="5", d="2024-01-02", tid=uuid.UUID(int=2)),
        _t(buy_in="5", prize="5", d="2024-01-03", tid=uuid.UUID(int=3)),  # break-even
        _t(buy_in="5", prize="0", d="2024-01-04", tid=uuid.UUID(int=4)),
        _t(buy_in="5", prize="0", d="2024-01-05", tid=uuid.UUID(int=5)),
    ]
    s = summarize(seq)
    assert s.longest_win_streak == 2
    assert s.longest_loss_streak == 2


# --- deterministic ordering ---

def test_chronological_orders_by_date_then_time_then_id():
    a = _t(d="2024-01-02", st="10:00", tid=uuid.UUID(int=10))
    b = _t(d="2024-01-01", st="22:00", tid=uuid.UUID(int=20))
    c = _t(d="2024-01-01", st="09:00", tid=uuid.UUID(int=30))
    ordered = chronological([a, b, c])
    assert [x.date.isoformat() for x in ordered] == ["2024-01-01", "2024-01-01", "2024-01-02"]
    # same date: earlier time first
    assert ordered[0].start_time == time(9, 0)
    assert ordered[1].start_time == time(22, 0)


def test_null_start_time_sorts_first_within_date():
    no_time = _t(d="2024-01-01", st=None, tid=uuid.UUID(int=1))
    with_time = _t(d="2024-01-01", st="08:00", tid=uuid.UUID(int=2))
    ordered = chronological([with_time, no_time])
    assert ordered[0] is no_time


# --- classification ---

def test_classify_half_open_intervals():
    roi_bands = [
        Band(None, Decimal("0"), "Perdedor"),
        Band(Decimal("0"), Decimal("10"), "Regular"),
        Band(Decimal("10"), Decimal("30"), "Bom"),
        Band(Decimal("30"), None, "Excelente"),
    ]
    assert classify(Decimal("-5"), roi_bands) == "Perdedor"
    assert classify(Decimal("0"), roi_bands) == "Regular"      # lower inclusive
    assert classify(Decimal("10"), roi_bands) == "Bom"         # boundary -> next band
    assert classify(Decimal("29.99"), roi_bands) == "Bom"
    assert classify(Decimal("30"), roi_bands) == "Excelente"
    assert classify(Decimal("1000"), roi_bands) == "Excelente"


def test_classify_none_value_returns_none():
    assert classify(None, [Band(None, None, "x")]) is None
