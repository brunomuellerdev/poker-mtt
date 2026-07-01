"""use clock_timestamp() for created_at (reliable insertion-moment ordering)

Revision ID: c4d3e2f1a0b9
Revises: b3c2d1e0f9a8
Create Date: 2026-06-29

func.now() returns the transaction timestamp (constant within a transaction),
so rows inserted in the same transaction tie on created_at. clock_timestamp()
advances per statement, giving a deterministic creation-order tiebreaker.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c4d3e2f1a0b9"
down_revision: str | None = "b3c2d1e0f9a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = ("users", "user_settings", "sessions", "tournaments", "hand_reviews")


def upgrade() -> None:
    for t in _TABLES:
        op.execute(
            f"ALTER TABLE {t} ALTER COLUMN created_at "
            f"SET DEFAULT clock_timestamp()"
        )


def downgrade() -> None:
    for t in _TABLES:
        op.execute(f"ALTER TABLE {t} ALTER COLUMN created_at SET DEFAULT now()")
