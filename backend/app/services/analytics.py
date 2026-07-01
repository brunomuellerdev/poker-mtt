import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.core.metrics.classification import classify
from app.core.metrics.engine import TournamentResult, summarize
from app.repositories.analytics import AnalyticsRepository, GroupRow, SeriesPoint
from app.repositories.evaluation import EvaluationRepository
from app.repositories.tournament import TournamentFilters, TournamentRepository

_CENTS = Decimal("0.01")
_HUNDRED = Decimal("100")


def _q(value: Decimal | None) -> Decimal | None:
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP) if value is not None else None


def _ratio(part: int, whole: int) -> Decimal | None:
    return (Decimal(part) / Decimal(whole) * _HUNDRED) if whole else None


def _roi(profit: Decimal, cost: Decimal) -> Decimal | None:
    return (profit / cost * _HUNDRED) if cost > 0 else None


def _group_to_dict(r: GroupRow) -> dict:
    return {
        "key": r.key,
        "tournaments": r.tournaments,
        "profit_base": _q(r.profit_base),
        "roi_pct": _q(_roi(r.profit_base, r.cost_base)),
        "itm_pct": _q(_ratio(r.itm_count, r.tournaments)),
        "final_table_pct": _q(_ratio(r.final_table_count, r.tournaments)),
        "win_pct": _q(_ratio(r.win_count, r.tournaments)),
    }


def _series_to_dict(p: SeriesPoint) -> dict:
    return {
        "period": p.period,
        "tournaments": p.tournaments,
        "profit_base": _q(p.profit_base),
        "roi_pct": _q(_roi(p.profit_base, p.cost_base)),
    }


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.analytics = AnalyticsRepository(db)
        self.evals = EvaluationRepository(db)
        self.tournaments = TournamentRepository(db)

    # category breakdowns
    def breakdown(self, user_id: uuid.UUID, dimension: str, f: TournamentFilters) -> list[dict]:
        fn = {
            "room": self.analytics.by_room,
            "buy_in": self.analytics.by_buy_in,
            "speed": self.analytics.by_speed,
            "tournament_type": self.analytics.by_tournament_type,
            "bounty_type": self.analytics.by_bounty_type,
            "weekday": self.analytics.by_weekday,
            "hour": self.analytics.by_hour,
        }[dimension]
        return [_group_to_dict(r) for r in fn(user_id, f)]

    def monthly(self, user_id: uuid.UUID, f: TournamentFilters) -> list[dict]:
        return [_series_to_dict(p) for p in self.analytics.monthly(user_id, f)]

    def yearly(self, user_id: uuid.UUID, f: TournamentFilters) -> list[dict]:
        return [_series_to_dict(p) for p in self.analytics.yearly(user_id, f)]

    def cumulative(self, user_id: uuid.UUID, f: TournamentFilters) -> list[dict]:
        return [
            {"date": p.date.isoformat(), "cumulative_base": _q(p.cumulative_base)}
            for p in self.analytics.cumulative_profit(user_id, f)
        ]

    def heatmap(self, user_id: uuid.UUID, f: TournamentFilters) -> list[dict]:
        return [
            {
                "weekday": c.weekday,
                "hour": c.hour,
                "tournaments": c.tournaments,
                "profit_base": _q(c.profit_base),
                "roi_pct": _q(_roi(c.profit_base, c.cost_base)),
            }
            for c in self.analytics.weekday_hour(user_id, f)
        ]

    def indicators(self, user_id: uuid.UUID, f: TournamentFilters) -> list[dict]:
        """Overall indicators (engine) with each value classified against the
        user's own evaluation bands."""
        s = self._summary(user_id, f)
        # (indicator_key, value)
        values: list[tuple[str, Decimal | None]] = [
            ("roi", _q(s.roi_pct)),
            ("itm", _q(s.itm_pct)),
            ("final_table_pct", _q(s.final_table_pct)),
            ("win_pct", _q(s.win_pct)),
            ("reliability", Decimal(s.tournaments)),
        ]
        out: list[dict] = []
        for key, value in values:
            bands = self.evals.bands(user_id, key)
            out.append(
                {
                    "indicator": key,
                    "value": value,
                    "classification": classify(value, bands),
                }
            )
        return out

    def _summary(self, user_id: uuid.UUID, f: TournamentFilters):
        rows = self.tournaments.list_for_metrics(user_id, f)
        return summarize(
            [
                TournamentResult(
                    id=t.id,
                    date=t.date,
                    start_time=t.start_time,
                    buy_in=t.buy_in,
                    rebuys=t.rebuys,
                    reentries=t.reentries,
                    addon_cost=t.addon_cost,
                    prize=t.prize,
                    bounty=t.bounty,
                    fx_rate_to_base=t.fx_rate_to_base,
                    final_position=t.final_position,
                    final_table_size=t.final_table_size,
                )
                for t in rows
            ]
        )


