"""Import all models so Base.metadata is fully populated for Alembic autogenerate."""

from app.db.base import Base
from app.db.models import (
    EvaluationRange,
    MarkedHand,
    Tag,
    Tournament,
    TournamentTag,
    User,
    UserSettings,
)

__all__ = [
    "Base",
    "EvaluationRange",
    "MarkedHand",
    "Tag",
    "Tournament",
    "TournamentTag",
    "User",
    "UserSettings",
]
