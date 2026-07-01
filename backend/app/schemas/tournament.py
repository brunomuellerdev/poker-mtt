import uuid
from datetime import date as date_type
from datetime import datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import (
    BettingStructure,
    BountyType,
    GameType,
    Speed,
    TournamentType,
)


class TournamentCreate(BaseModel):
    date: date_type
    start_time: time | None = None
    poker_room: str = Field(min_length=1, max_length=100)
    tournament_name: str | None = Field(default=None, max_length=255)

    game_type: GameType
    betting_structure: BettingStructure
    speed: Speed = Speed.REGULAR
    tournament_type: TournamentType = TournamentType.NORMAL
    allows_rebuy: bool = False
    allows_reentry: bool = False
    allows_addon: bool = False
    bounty_type: BountyType = BountyType.NONE

    table_size: int = Field(default=9, ge=2, le=10)
    # if omitted, service sets it from table_size
    final_table_size: int | None = Field(default=None, ge=2, le=10)

    currency: str = Field(default="USD", min_length=3, max_length=3)
    fx_rate_to_base: Decimal = Field(default=Decimal("1.0"), gt=0)

    buy_in: Decimal = Field(ge=0)
    addon_cost: Decimal = Field(default=Decimal("0"), ge=0)
    guarantee: Decimal | None = Field(default=None, ge=0)
    prize: Decimal = Field(default=Decimal("0"), ge=0)
    bounty: Decimal = Field(default=Decimal("0"), ge=0)

    rebuys: int = Field(default=0, ge=0)
    reentries: int = Field(default=0, ge=0)
    add_ons: int = Field(default=0, ge=0)

    entrants: int = Field(ge=1)
    final_position: int = Field(ge=1)
    duration_minutes: int | None = Field(default=None, ge=0)
    notes: str | None = None
    tag_ids: list[uuid.UUID] = Field(default_factory=list)


class TournamentUpdate(BaseModel):
    # all optional; only provided fields are changed
    date: date_type | None = None
    start_time: time | None = None
    poker_room: str | None = Field(default=None, min_length=1, max_length=100)
    tournament_name: str | None = Field(default=None, max_length=255)
    game_type: GameType | None = None
    betting_structure: BettingStructure | None = None
    speed: Speed | None = None
    tournament_type: TournamentType | None = None
    allows_rebuy: bool | None = None
    allows_reentry: bool | None = None
    allows_addon: bool | None = None
    bounty_type: BountyType | None = None
    table_size: int | None = Field(default=None, ge=2, le=10)
    final_table_size: int | None = Field(default=None, ge=2, le=10)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    fx_rate_to_base: Decimal | None = Field(default=None, gt=0)
    buy_in: Decimal | None = Field(default=None, ge=0)
    addon_cost: Decimal | None = Field(default=None, ge=0)
    guarantee: Decimal | None = Field(default=None, ge=0)
    prize: Decimal | None = Field(default=None, ge=0)
    bounty: Decimal | None = Field(default=None, ge=0)
    rebuys: int | None = Field(default=None, ge=0)
    reentries: int | None = Field(default=None, ge=0)
    add_ons: int | None = Field(default=None, ge=0)
    entrants: int | None = Field(default=None, ge=1)
    final_position: int | None = Field(default=None, ge=1)
    duration_minutes: int | None = Field(default=None, ge=0)
    notes: str | None = None
    tag_ids: list[uuid.UUID] | None = None


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str


class TournamentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    date: date_type
    start_time: time | None
    poker_room: str
    tournament_name: str | None
    game_type: GameType
    betting_structure: BettingStructure
    speed: Speed
    tournament_type: TournamentType
    allows_rebuy: bool
    allows_reentry: bool
    allows_addon: bool
    bounty_type: BountyType
    table_size: int
    final_table_size: int
    currency: str
    fx_rate_to_base: Decimal
    buy_in: Decimal
    addon_cost: Decimal
    guarantee: Decimal | None
    prize: Decimal
    bounty: Decimal
    rebuys: int
    reentries: int
    add_ons: int
    entrants: int
    final_position: int
    duration_minutes: int | None
    notes: str | None
    # computed columns (read-only, from DB)
    total_cost: Decimal
    total_winnings: Decimal
    profit_native: Decimal
    profit_base: Decimal
    itm: bool
    winner: bool
    final_table: bool
    tags: list[TagOut]
    created_at: datetime
    updated_at: datetime
