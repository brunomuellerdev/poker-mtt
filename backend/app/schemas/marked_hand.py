import uuid
from datetime import date as date_type
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MarkedHandCreate(BaseModel):
    hand_code: str = Field(min_length=1, max_length=100)
    poker_room: str = Field(min_length=1, max_length=100)
    date: date_type
    # optional replay payload (full parsed hand dict) when marked from replayer
    replay: dict[str, Any] | None = None


class MarkedHandUpdate(BaseModel):
    hand_code: str | None = Field(default=None, min_length=1, max_length=100)
    poker_room: str | None = Field(default=None, min_length=1, max_length=100)
    date: date_type | None = None


class MarkedHandOut(BaseModel):
    """Lightweight list item — never includes the full replay payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hand_code: str
    poker_room: str
    date: date_type
    hero_cards: list[str] | None = None
    board: list[str] | None = None
    has_replay: bool = False


class MarkedHandReplayOut(BaseModel):
    id: uuid.UUID
    hand_code: str
    replay: dict[str, Any] | None
