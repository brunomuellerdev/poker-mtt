"""add replay payload to marked_hands

Revision ID: e6f5a4b3c2d1
Revises: d5e4f3a2b1c0
Create Date: 2026-06-30

Marked hands become the persistence for the replayer: when marked from the
replayer, the full parsed hand (frames) is stored so it can be replayed without
the original file. hero_cards/board are stored for the list without loading the
big replay JSON.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "e6f5a4b3c2d1"
down_revision: str | None = "d5e4f3a2b1c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("marked_hands", sa.Column("replay", JSONB(), nullable=True))
    op.add_column("marked_hands", sa.Column("hero_cards", JSONB(), nullable=True))
    op.add_column("marked_hands", sa.Column("board", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("marked_hands", "board")
    op.drop_column("marked_hands", "hero_cards")
    op.drop_column("marked_hands", "replay")
