"""drop sessions and hand_reviews, add marked_hands

Revision ID: d5e4f3a2b1c0
Revises: c4d3e2f1a0b9
Create Date: 2026-06-30

Sessions removed (feature dropped). hand_reviews was speculative Phase-1 schema
never wired to API/UI; replaced by the standalone marked_hands feature
(hand identifier + room + date, not tied to a tournament).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d5e4f3a2b1c0"
down_revision: str | None = "c4d3e2f1a0b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # tournaments.session_id FK -> drop column
    op.drop_column("tournaments", "session_id")
    op.drop_table("hand_reviews")
    op.drop_table("sessions")

    op.create_table(
        "marked_hands",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("hand_code", sa.String(length=100), nullable=False),
        sa.Column("poker_room", sa.String(length=100), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_marked_hands_user_date", "marked_hands", ["user_id", "date"]
    )


def downgrade() -> None:
    op.drop_index("ix_marked_hands_user_date", table_name="marked_hands")
    op.drop_table("marked_hands")

    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("average_tables", sa.SmallInteger(), nullable=True),
        sa.Column("concentration_level", sa.SmallInteger(), nullable=True),
        sa.Column("emotional_state", sa.String(length=20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("clock_timestamp()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "tournaments",
        sa.Column(
            "session_id",
            sa.Uuid(),
            sa.ForeignKey("sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_table(
        "hand_reviews",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("tournament_id", sa.Uuid(), sa.ForeignKey("tournaments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("solved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("clock_timestamp()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
