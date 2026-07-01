import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import ColumnElement, Select, select
from sqlalchemy.orm import Session, selectinload

from app.core.pagination import Page
from app.db.enums import BountyType, Speed, TournamentStatus, TournamentType
from app.db.models import Tag, Tournament


@dataclass(frozen=True, slots=True)
class TournamentFilters:
    date_from: date | None = None
    date_to: date | None = None
    poker_room: str | None = None
    tournament_type: TournamentType | None = None
    speed: Speed | None = None
    bounty_type: BountyType | None = None
    buy_in_min: Decimal | None = None
    buy_in_max: Decimal | None = None
    itm: bool | None = None
    tag_ids: list[uuid.UUID] | None = None


def filter_clauses(
    user_id: uuid.UUID, f: TournamentFilters, completed_only: bool = False
) -> list[ColumnElement[bool]]:
    """Shared WHERE conditions — reused by CRUD listing and analytics aggregation.

    completed_only=True excludes 'registered' tournaments (no result yet), which
    must never enter metrics. Listing uses the default (shows registered too).
    """
    clauses: list[ColumnElement[bool]] = [Tournament.user_id == user_id]
    if completed_only:
        clauses.append(Tournament.status == TournamentStatus.COMPLETED)
    if f.date_from is not None:
        clauses.append(Tournament.date >= f.date_from)
    if f.date_to is not None:
        clauses.append(Tournament.date <= f.date_to)
    if f.poker_room is not None:
        clauses.append(Tournament.poker_room == f.poker_room)
    if f.tournament_type is not None:
        clauses.append(Tournament.tournament_type == f.tournament_type)
    if f.speed is not None:
        clauses.append(Tournament.speed == f.speed)
    if f.bounty_type is not None:
        clauses.append(Tournament.bounty_type == f.bounty_type)
    if f.buy_in_min is not None:
        clauses.append(Tournament.buy_in >= f.buy_in_min)
    if f.buy_in_max is not None:
        clauses.append(Tournament.buy_in <= f.buy_in_max)
    if f.itm is not None:
        clauses.append(Tournament.itm == f.itm)
    if f.tag_ids:
        clauses.append(Tournament.tags.any(Tag.id.in_(f.tag_ids)))
    return clauses


class TournamentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: uuid.UUID, tournament_id: uuid.UUID) -> Tournament | None:
        stmt = (
            select(Tournament)
            .where(Tournament.id == tournament_id, Tournament.user_id == user_id)
            .options(selectinload(Tournament.tags))
        )
        return self.db.scalar(stmt)

    def add(self, tournament: Tournament) -> Tournament:
        self.db.add(tournament)
        self.db.flush()
        return tournament

    def delete(self, tournament: Tournament) -> None:
        self.db.delete(tournament)

    def get_tags(self, user_id: uuid.UUID, tag_ids: list[uuid.UUID]) -> list[Tag]:
        if not tag_ids:
            return []
        stmt = select(Tag).where(Tag.user_id == user_id, Tag.id.in_(tag_ids))
        return list(self.db.scalars(stmt))

    def _apply_filters(
        self, stmt: Select, user_id: uuid.UUID, f: TournamentFilters
    ) -> Select:
        return stmt.where(*filter_clauses(user_id, f))

    def list_offset(
        self,
        user_id: uuid.UUID,
        filters: TournamentFilters,
        limit: int,
        offset: int,
    ) -> Page[Tournament]:
        stmt = select(Tournament).options(selectinload(Tournament.tags))
        stmt = self._apply_filters(stmt, user_id, filters)
        # newest first: by tournament date+time, then by creation time as tiebreak.
        # start_time may be NULL -> sort those below same-day timed tournaments.
        stmt = stmt.order_by(
            Tournament.date.desc(),
            Tournament.start_time.desc().nulls_last(),
            Tournament.created_at.desc(),
        )
        stmt = stmt.offset(offset).limit(limit + 1)  # one extra to detect has_more

        rows = list(self.db.scalars(stmt))
        has_more = len(rows) > limit
        items = rows[:limit]
        next_offset = offset + limit if has_more else None
        return Page(items=items, has_more=has_more, next_offset=next_offset)

    def list_for_metrics(
        self, user_id: uuid.UUID, filters: TournamentFilters
    ) -> list[Tournament]:
        """Full (unpaginated) result set for aggregate metrics."""
        stmt = select(Tournament).where(*filter_clauses(user_id, filters, completed_only=True))
        return list(self.db.scalars(stmt))
