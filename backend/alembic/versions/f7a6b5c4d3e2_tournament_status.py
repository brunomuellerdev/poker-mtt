"""add tournament status (registered/completed); nullable result fields

Revision ID: f7a6b5c4d3e2
Revises: e6f5a4b3c2d1
Create Date: 2026-07-01

A 'registered' tournament is only signed up (no result yet) and is excluded
from all metrics. entrants/final_position/prize/bounty become nullable so a
registered tournament can be saved with empty results and completed later.
Existing rows are backfilled to 'completed'.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f7a6b5c4d3e2"
down_revision: str | None = "e6f5a4b3c2d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tournaments",
        sa.Column(
            "status",
            sa.String(length=12),
            nullable=False,
            server_default="completed",
        ),
    )
    op.create_check_constraint(
        "ck_tour_status",
        "tournaments",
        "status IN ('registered', 'completed')",
    )
    # result fields become nullable
    op.alter_column("tournaments", "entrants", existing_type=sa.Integer(), nullable=True)
    op.alter_column(
        "tournaments", "final_position", existing_type=sa.Integer(), nullable=True
    )
    op.alter_column(
        "tournaments", "prize", existing_type=sa.Numeric(14, 2), nullable=True
    )
    op.alter_column(
        "tournaments", "bounty", existing_type=sa.Numeric(14, 2), nullable=True
    )

    # Recreate generated columns that reference now-nullable inputs so they
    # COALESCE to sensible non-null values (they are NOT NULL columns).
    _COST = "buy_in * (1 + rebuys + reentries) + addon_cost"
    _WIN = "COALESCE(prize, 0) + COALESCE(bounty, 0)"
    for col in ("total_winnings", "profit_native", "profit_base", "itm", "winner", "final_table"):
        op.drop_column("tournaments", col)
    op.add_column(
        "tournaments",
        sa.Column(
            "total_winnings",
            sa.Numeric(16, 2),
            sa.Computed(_WIN, persisted=True),
        ),
    )
    op.add_column(
        "tournaments",
        sa.Column(
            "profit_native",
            sa.Numeric(16, 2),
            sa.Computed(f"({_WIN}) - ({_COST})", persisted=True),
        ),
    )
    op.add_column(
        "tournaments",
        sa.Column(
            "profit_base",
            sa.Numeric(18, 2),
            sa.Computed(
                f"(({_WIN}) - ({_COST})) * fx_rate_to_base", persisted=True
            ),
        ),
    )
    # dropping profit_base removed this index; recreate it
    op.create_index(
        "ix_tournaments_user_profit", "tournaments", ["user_id", "profit_base"]
    )
    op.add_column(
        "tournaments",
        sa.Column(
            "itm",
            sa.Boolean(),
            sa.Computed("COALESCE(prize > 0, false)", persisted=True),
        ),
    )
    op.add_column(
        "tournaments",
        sa.Column(
            "winner",
            sa.Boolean(),
            sa.Computed("COALESCE(final_position = 1, false)", persisted=True),
        ),
    )
    op.add_column(
        "tournaments",
        sa.Column(
            "final_table",
            sa.Boolean(),
            sa.Computed(
                "COALESCE(final_position <= final_table_size, false)",
                persisted=True,
            ),
        ),
    )


def downgrade() -> None:
    # restore original generated columns (without COALESCE)
    _COST = "buy_in * (1 + rebuys + reentries) + addon_cost"
    _WIN = "prize + bounty"
    for col in ("total_winnings", "profit_native", "profit_base", "itm", "winner", "final_table"):
        op.drop_column("tournaments", col)
    # restore NOT NULL (backfill nulls first to be safe)
    op.execute("UPDATE tournaments SET entrants = 0 WHERE entrants IS NULL")
    op.execute("UPDATE tournaments SET final_position = 0 WHERE final_position IS NULL")
    op.execute("UPDATE tournaments SET prize = 0 WHERE prize IS NULL")
    op.execute("UPDATE tournaments SET bounty = 0 WHERE bounty IS NULL")
    op.add_column(
        "tournaments",
        sa.Column("total_winnings", sa.Numeric(16, 2), sa.Computed(_WIN, persisted=True)),
    )
    op.add_column(
        "tournaments",
        sa.Column("profit_native", sa.Numeric(16, 2), sa.Computed(f"({_WIN}) - ({_COST})", persisted=True)),
    )
    op.add_column(
        "tournaments",
        sa.Column("profit_base", sa.Numeric(18, 2), sa.Computed(f"(({_WIN}) - ({_COST})) * fx_rate_to_base", persisted=True)),
    )
    op.create_index(
        "ix_tournaments_user_profit", "tournaments", ["user_id", "profit_base"]
    )
    op.add_column(
        "tournaments",
        sa.Column("itm", sa.Boolean(), sa.Computed("prize > 0", persisted=True)),
    )
    op.add_column(
        "tournaments",
        sa.Column("winner", sa.Boolean(), sa.Computed("final_position = 1", persisted=True)),
    )
    op.add_column(
        "tournaments",
        sa.Column("final_table", sa.Boolean(), sa.Computed("final_position <= final_table_size", persisted=True)),
    )
    op.alter_column(
        "tournaments", "bounty", existing_type=sa.Numeric(14, 2), nullable=False
    )
    op.alter_column(
        "tournaments", "prize", existing_type=sa.Numeric(14, 2), nullable=False
    )
    op.alter_column(
        "tournaments", "final_position", existing_type=sa.Integer(), nullable=False
    )
    op.alter_column(
        "tournaments", "entrants", existing_type=sa.Integer(), nullable=False
    )
    op.drop_constraint("ck_tour_status", "tournaments", type_="check")
    op.drop_column("tournaments", "status")
