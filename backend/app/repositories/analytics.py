"""SQL-side analytics — time series via window functions, category breakdowns
via GROUP BY. Ratios (ROI%, ITM%) are returned as raw sums/counts and divided
in Decimal by the caller to avoid float rounding."""

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import ColumnElement, Integer, cast, extract, func, select
from sqlalchemy.orm import Session

from app.db.models import Tournament
from app.repositories.tournament import TournamentFilters, filter_clauses

# total cost converted to base currency (generated column is native)
_COST_BASE = Tournament.total_cost * Tournament.fx_rate_to_base


@dataclass(frozen=True, slots=True)
class GroupRow:
    key: str
    tournaments: int
    profit_base: Decimal
    cost_base: Decimal
    itm_count: int
    final_table_count: int
    win_count: int


@dataclass(frozen=True, slots=True)
class SeriesPoint:
    period: str
    profit_base: Decimal
    cost_base: Decimal
    tournaments: int


@dataclass(frozen=True, slots=True)
class CumulativePoint:
    date: date
    cumulative_base: Decimal


@dataclass(frozen=True, slots=True)
class HeatmapCell:
    weekday: int  # 1=Mon .. 7=Sun
    hour: int     # 0..23
    tournaments: int
    profit_base: Decimal
    cost_base: Decimal


class AnalyticsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- grouped breakdowns ---

    def _grouped(
        self,
        user_id: uuid.UUID,
        filters: TournamentFilters,
        key_expr: ColumnElement,
    ) -> list[GroupRow]:
        stmt = (
            select(
                key_expr.label("key"),
                func.count().label("tournaments"),
                func.coalesce(func.sum(Tournament.profit_base), 0).label("profit"),
                func.coalesce(func.sum(_COST_BASE), 0).label("cost"),
                func.count().filter(Tournament.itm).label("itm_count"),
                func.count().filter(Tournament.final_table).label("ft_count"),
                func.count().filter(Tournament.winner).label("win_count"),
            )
            .where(*filter_clauses(user_id, filters))
            .group_by(key_expr)
            .order_by(key_expr)
        )
        return [
            GroupRow(
                key=str(r.key),
                tournaments=r.tournaments,
                profit_base=Decimal(r.profit),
                cost_base=Decimal(r.cost),
                itm_count=r.itm_count,
                final_table_count=r.ft_count,
                win_count=r.win_count,
            )
            for r in self.db.execute(stmt)
        ]

    def by_room(self, uid, f) -> list[GroupRow]:
        return self._grouped(uid, f, Tournament.poker_room)

    def by_buy_in(self, uid, f) -> list[GroupRow]:
        return self._grouped(uid, f, cast(Tournament.buy_in, Integer))

    def by_speed(self, uid, f) -> list[GroupRow]:
        return self._grouped(uid, f, Tournament.speed)

    def by_tournament_type(self, uid, f) -> list[GroupRow]:
        return self._grouped(uid, f, Tournament.tournament_type)

    def by_bounty_type(self, uid, f) -> list[GroupRow]:
        return self._grouped(uid, f, Tournament.bounty_type)

    def by_weekday(self, uid, f) -> list[GroupRow]:
        # ISO day of week: 1=Monday .. 7=Sunday
        return self._grouped(uid, f, cast(extract("isodow", Tournament.date), Integer))

    def by_hour(self, uid, f) -> list[GroupRow]:
        return self._grouped(
            uid, f, cast(extract("hour", Tournament.start_time), Integer)
        )

    # --- time series ---

    def monthly(self, uid, f) -> list[SeriesPoint]:
        period = func.to_char(
            func.date_trunc("month", Tournament.date), "YYYY-MM"
        )
        return self._series(uid, f, period)

    def yearly(self, uid, f) -> list[SeriesPoint]:
        period = func.to_char(func.date_trunc("year", Tournament.date), "YYYY")
        return self._series(uid, f, period)

    def _series(self, user_id, filters, period_expr) -> list[SeriesPoint]:
        stmt = (
            select(
                period_expr.label("period"),
                func.coalesce(func.sum(Tournament.profit_base), 0).label("profit"),
                func.coalesce(func.sum(_COST_BASE), 0).label("cost"),
                func.count().label("tournaments"),
            )
            .where(*filter_clauses(user_id, filters))
            .group_by(period_expr)
            .order_by(period_expr)
        )
        return [
            SeriesPoint(
                period=r.period,
                profit_base=Decimal(r.profit),
                cost_base=Decimal(r.cost),
                tournaments=r.tournaments,
            )
            for r in self.db.execute(stmt)
        ]

    def cumulative_profit(self, user_id, filters) -> list[CumulativePoint]:
        """Running profit in base currency, ordered chronologically (window fn)."""
        running = func.sum(Tournament.profit_base).over(
            order_by=[
                Tournament.date,
                Tournament.start_time.nulls_first(),
                Tournament.id,
            ]
        )
        stmt = (
            select(Tournament.date, running.label("cumulative"))
            .where(*filter_clauses(user_id, filters))
            .order_by(
                Tournament.date,
                Tournament.start_time.nulls_first(),
                Tournament.id,
            )
        )
        return [
            CumulativePoint(date=r.date, cumulative_base=Decimal(r.cumulative))
            for r in self.db.execute(stmt)
        ]

    def weekday_hour(self, user_id, filters) -> list[HeatmapCell]:
        """2D grid: ISO weekday (1-7) x hour (0-23). Rows with NULL start_time
        are excluded (no hour to bucket)."""
        weekday = cast(extract("isodow", Tournament.date), Integer)
        hour = cast(extract("hour", Tournament.start_time), Integer)
        stmt = (
            select(
                weekday.label("weekday"),
                hour.label("hour"),
                func.count().label("tournaments"),
                func.coalesce(func.sum(Tournament.profit_base), 0).label("profit"),
                func.coalesce(func.sum(_COST_BASE), 0).label("cost"),
            )
            .where(*filter_clauses(user_id, filters))
            .where(Tournament.start_time.is_not(None))
            .group_by(weekday, hour)
        )
        return [
            HeatmapCell(
                weekday=r.weekday,
                hour=r.hour,
                tournaments=r.tournaments,
                profit_base=Decimal(r.profit),
                cost_base=Decimal(r.cost),
            )
            for r in self.db.execute(stmt)
        ]
