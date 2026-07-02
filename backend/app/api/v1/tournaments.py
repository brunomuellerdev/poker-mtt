import uuid
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.core.metrics.engine import TournamentResult, summarize
from app.db.enums import BountyType, Speed, TournamentType
from app.db.models import Tournament
from app.repositories.tournament import TournamentFilters, TournamentRepository
from app.schemas.common import PageOut
from app.schemas.tournament import (
    TournamentCreate,
    TournamentOut,
    TournamentUpdate,
)
from app.services.tournament import (
    InvalidTagReference,
    TournamentNotFound,
    TournamentService,
)

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


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
    tag_ids: Annotated[list[uuid.UUID] | None, Query()] = None,
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
        tag_ids=tag_ids,
    )


def _to_result(t: Tournament) -> TournamentResult:
    return TournamentResult(
        id=t.id,
        date=t.date,
        start_time=t.start_time,
        buy_in=t.buy_in,
        rebuys=t.rebuys,
        reentries=t.reentries,
        addon_cost=t.addon_cost,
        prize=t.prize,  # None (registered) normalized in TournamentResult
        bounty=t.bounty,
        fx_rate_to_base=t.fx_rate_to_base,
        final_position=t.final_position,
        final_table_size=t.final_table_size,
    )


@router.post("", response_model=TournamentOut, status_code=status.HTTP_201_CREATED)
def create_tournament(
    data: TournamentCreate, current_user: CurrentUser, db: DbSession
) -> TournamentOut:
    try:
        t = TournamentService(db).create(current_user.id, data)
    except InvalidTagReference as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more tags do not exist",
        ) from exc
    return TournamentOut.model_validate(t)


@router.get("", response_model=PageOut[TournamentOut])
def list_tournaments(
    current_user: CurrentUser,
    db: DbSession,
    filters: Annotated[TournamentFilters, Depends(_filters)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PageOut[TournamentOut]:
    page = TournamentRepository(db).list_offset(
        current_user.id, filters, limit, offset
    )
    return PageOut[TournamentOut](
        items=[TournamentOut.model_validate(t) for t in page.items],
        next_offset=page.next_offset,
        has_more=page.has_more,
    )


_CENTS = Decimal("0.01")


def _money(value: Decimal | None) -> Decimal | None:
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP) if value is not None else None


@router.get("/summary")
def tournaments_summary(
    current_user: CurrentUser,
    db: DbSession,
    filters: Annotated[TournamentFilters, Depends(_filters)],
) -> dict:
    rows = TournamentRepository(db).list_for_metrics(current_user.id, filters)
    s = summarize([_to_result(t) for t in rows])
    return {
        "tournaments": s.tournaments,
        "total_buyins_base": _money(s.total_buyins_base),
        "total_prize_base": _money(s.total_prize_base),
        "total_bounty_base": _money(s.total_bounty_base),
        "total_profit_base": _money(s.total_profit_base),
        "roi_pct": _money(s.roi_pct),
        "abi_base": _money(s.abi_base),
        "itm_pct": _money(s.itm_pct),
        "final_table_pct": _money(s.final_table_pct),
        "win_pct": _money(s.win_pct),
        "largest_prize_base": _money(s.largest_prize_base),
        "largest_profit_base": _money(s.largest_profit_base),
        "largest_loss_base": _money(s.largest_loss_base),
        "max_drawdown_base": _money(s.max_drawdown_base),
        "max_upswing_base": _money(s.max_upswing_base),
        "longest_win_streak": s.longest_win_streak,
        "longest_loss_streak": s.longest_loss_streak,
    }


@router.get("/{tournament_id}", response_model=TournamentOut)
def get_tournament(
    tournament_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> TournamentOut:
    t = TournamentRepository(db).get(current_user.id, tournament_id)
    if t is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found"
        )
    return TournamentOut.model_validate(t)


@router.patch("/{tournament_id}", response_model=TournamentOut)
def update_tournament(
    tournament_id: uuid.UUID,
    data: TournamentUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> TournamentOut:
    try:
        t = TournamentService(db).update(current_user.id, tournament_id, data)
    except TournamentNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found"
        ) from exc
    except InvalidTagReference as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more tags do not exist",
        ) from exc
    return TournamentOut.model_validate(t)


@router.delete("/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tournament(
    tournament_id: uuid.UUID, current_user: CurrentUser, db: DbSession
) -> None:
    try:
        TournamentService(db).delete(current_user.id, tournament_id)
    except TournamentNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tournament not found"
        ) from exc
