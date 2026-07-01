from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.db.enums import BountyType, Speed, TournamentType
from app.repositories.tournament import TournamentFilters
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

_DIMENSIONS = {
    "room",
    "buy_in",
    "speed",
    "tournament_type",
    "bounty_type",
    "weekday",
    "hour",
}


def _filters(
    date_from: date | None = None,
    date_to: date | None = None,
    poker_room: str | None = None,
    tournament_type: TournamentType | None = None,
    speed: Speed | None = None,
    bounty_type: BountyType | None = None,
    buy_in_min: Decimal | None = None,
    buy_in_max: Decimal | None = None,
    itm: bool | None = None,
) -> TournamentFilters:
    return TournamentFilters(
        date_from=date_from,
        date_to=date_to,
        poker_room=poker_room,
        tournament_type=tournament_type,
        speed=speed,
        bounty_type=bounty_type,
        buy_in_min=buy_in_min,
        buy_in_max=buy_in_max,
        itm=itm,
    )


Filters = Annotated[TournamentFilters, Depends(_filters)]


@router.get("/breakdown")
def breakdown(
    current_user: CurrentUser,
    db: DbSession,
    filters: Filters,
    by: Annotated[str, Query()],
) -> list[dict]:
    if by not in _DIMENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid dimension. Allowed: {sorted(_DIMENSIONS)}",
        )
    return AnalyticsService(db).breakdown(current_user.id, by, filters)


@router.get("/timeseries/monthly")
def monthly(current_user: CurrentUser, db: DbSession, filters: Filters) -> list[dict]:
    return AnalyticsService(db).monthly(current_user.id, filters)


@router.get("/timeseries/yearly")
def yearly(current_user: CurrentUser, db: DbSession, filters: Filters) -> list[dict]:
    return AnalyticsService(db).yearly(current_user.id, filters)


@router.get("/timeseries/cumulative")
def cumulative(current_user: CurrentUser, db: DbSession, filters: Filters) -> list[dict]:
    return AnalyticsService(db).cumulative(current_user.id, filters)


@router.get("/heatmap")
def heatmap(current_user: CurrentUser, db: DbSession, filters: Filters) -> list[dict]:
    return AnalyticsService(db).heatmap(current_user.id, filters)


@router.get("/indicators")
def indicators(current_user: CurrentUser, db: DbSession, filters: Filters) -> list[dict]:
    return AnalyticsService(db).indicators(current_user.id, filters)
