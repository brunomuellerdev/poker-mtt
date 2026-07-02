"""Pure calculation engine — no SQLAlchemy, no I/O.

All monetary aggregation is done in the user's BASE currency. Each tournament
carries `fx_rate_to_base` (1.0 for single-currency users); native amounts are
multiplied by it before summing. Ratios (ROI per tournament, ITM%, streaks) are
currency-invariant and need no conversion, but aggregate ROI sums absolute
values so it is computed in base.

Chronological order for cumulative/streak/drawdown series is deterministic:
(date, start_time, id), with NULL start_time sorted as the earliest time.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal

_ZERO = Decimal("0")
_HUNDRED = Decimal("100")


@dataclass(frozen=True, slots=True)
class TournamentResult:
    """Minimal projection of a tournament needed for metrics."""

    id: uuid.UUID
    date: date
    start_time: time | None
    buy_in: Decimal
    rebuys: int
    reentries: int
    addon_cost: Decimal
    prize: Decimal | None
    bounty: Decimal | None
    fx_rate_to_base: Decimal
    final_position: int | None
    final_table_size: int

    def __post_init__(self) -> None:
        # nullable in DB for 'registered' tournaments; normalize so every
        # downstream calc operates on non-null values regardless of caller
        if self.prize is None:
            object.__setattr__(self, "prize", _ZERO)
        if self.bounty is None:
            object.__setattr__(self, "bounty", _ZERO)
        if self.final_position is None:
            object.__setattr__(self, "final_position", 0)


# --- per-tournament (native) ---

def total_cost_native(t: TournamentResult) -> Decimal:
    return t.buy_in * (1 + t.rebuys + t.reentries) + t.addon_cost


def total_winnings(t: TournamentResult) -> Decimal:
    """Position prize plus bounty (knockout) winnings."""
    return t.prize + t.bounty


def profit_native(t: TournamentResult) -> Decimal:
    return total_winnings(t) - total_cost_native(t)


# --- per-tournament (base) ---

def total_cost_base(t: TournamentResult) -> Decimal:
    return total_cost_native(t) * t.fx_rate_to_base


def profit_base(t: TournamentResult) -> Decimal:
    return profit_native(t) * t.fx_rate_to_base


def buyin_base(t: TournamentResult) -> Decimal:
    return t.buy_in * t.fx_rate_to_base


def is_itm(t: TournamentResult) -> bool:
    return t.prize > _ZERO


def is_winner(t: TournamentResult) -> bool:
    return t.final_position == 1


def is_final_table(t: TournamentResult) -> bool:
    return t.final_position <= t.final_table_size


# --- ordering ---

def chronological(results: list[TournamentResult]) -> list[TournamentResult]:
    """Stable, reproducible order for series-dependent metrics."""
    return sorted(
        results,
        key=lambda t: (t.date, t.start_time or time.min, t.id.hex),
    )


# --- aggregates ---

@dataclass(frozen=True, slots=True)
class Summary:
    tournaments: int
    total_buyins_base: Decimal       # sum of total cost (incl. rebuys/addons), base
    total_prize_base: Decimal
    total_bounty_base: Decimal
    total_profit_base: Decimal
    roi_pct: Decimal | None          # None when no cost (undefined)
    abi_base: Decimal | None         # average buy-in (entry only), base
    itm_pct: Decimal | None
    final_table_pct: Decimal | None
    win_pct: Decimal | None
    largest_prize_base: Decimal | None
    largest_profit_base: Decimal | None
    largest_loss_base: Decimal | None
    max_drawdown_base: Decimal
    max_upswing_base: Decimal
    longest_win_streak: int
    longest_loss_streak: int


def _pct(part: int, whole: int) -> Decimal | None:
    if whole == 0:
        return None
    return (Decimal(part) / Decimal(whole)) * _HUNDRED


def cumulative_profit(results: list[TournamentResult]) -> list[Decimal]:
    """Running sum of profit_base in chronological order."""
    running = _ZERO
    series: list[Decimal] = []
    for t in chronological(results):
        running += profit_base(t)
        series.append(running)
    return series


def max_drawdown(series: list[Decimal]) -> Decimal:
    """Largest peak-to-trough drop in the cumulative series (>= 0)."""
    peak = _ZERO
    worst = _ZERO
    for value in series:
        peak = max(peak, value)
        worst = max(worst, peak - value)
    return worst


def max_upswing(series: list[Decimal]) -> Decimal:
    """Largest trough-to-peak rise in the cumulative series (>= 0)."""
    trough = _ZERO
    best = _ZERO
    for value in series:
        trough = min(trough, value)
        best = max(best, value - trough)
    return best


def _streaks(results: list[TournamentResult]) -> tuple[int, int]:
    """Longest consecutive winning / losing runs. Break-even (0) breaks both."""
    longest_win = longest_loss = 0
    cur_win = cur_loss = 0
    for t in chronological(results):
        p = profit_base(t)
        if p > _ZERO:
            cur_win += 1
            cur_loss = 0
        elif p < _ZERO:
            cur_loss += 1
            cur_win = 0
        else:
            cur_win = cur_loss = 0
        longest_win = max(longest_win, cur_win)
        longest_loss = max(longest_loss, cur_loss)
    return longest_win, longest_loss


def summarize(results: list[TournamentResult]) -> Summary:
    n = len(results)
    if n == 0:
        return Summary(
            tournaments=0,
            total_buyins_base=_ZERO,
            total_prize_base=_ZERO,
            total_bounty_base=_ZERO,
            total_profit_base=_ZERO,
            roi_pct=None,
            abi_base=None,
            itm_pct=None,
            final_table_pct=None,
            win_pct=None,
            largest_prize_base=None,
            largest_profit_base=None,
            largest_loss_base=None,
            max_drawdown_base=_ZERO,
            max_upswing_base=_ZERO,
            longest_win_streak=0,
            longest_loss_streak=0,
        )

    total_cost = sum((total_cost_base(t) for t in results), _ZERO)
    total_prize = sum((t.prize * t.fx_rate_to_base for t in results), _ZERO)
    total_bounty = sum((t.bounty * t.fx_rate_to_base for t in results), _ZERO)
    total_profit = sum((profit_base(t) for t in results), _ZERO)
    profits = [profit_base(t) for t in results]
    prizes = [t.prize * t.fx_rate_to_base for t in results]

    series = cumulative_profit(results)
    win_streak, loss_streak = _streaks(results)

    return Summary(
        tournaments=n,
        total_buyins_base=total_cost,
        total_prize_base=total_prize,
        total_bounty_base=total_bounty,
        total_profit_base=total_profit,
        roi_pct=(total_profit / total_cost * _HUNDRED) if total_cost > _ZERO else None,
        abi_base=sum((buyin_base(t) for t in results), _ZERO) / n,
        itm_pct=_pct(sum(1 for t in results if is_itm(t)), n),
        final_table_pct=_pct(sum(1 for t in results if is_final_table(t)), n),
        win_pct=_pct(sum(1 for t in results if is_winner(t)), n),
        largest_prize_base=max(prizes),
        largest_profit_base=max(profits),
        largest_loss_base=min(profits),
        max_drawdown_base=max_drawdown(series),
        max_upswing_base=max_upswing(series),
        longest_win_streak=win_streak,
        longest_loss_streak=loss_streak,
    )
