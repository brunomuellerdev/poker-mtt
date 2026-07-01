"""add bounty winnings and recompute profit columns

Revision ID: a2b1c0d4e5f6
Revises: 1e31f3f4b909
Create Date: 2026-06-27

Bounty (knockout) winnings are earned per elimination, independent of reaching
the money. Profit must include bounty; ITM must NOT (it reflects the position
prize only). Generated-column expressions can't be altered in place in Postgres,
so the dependent columns are dropped and re-created.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a2b1c0d4e5f6"
down_revision: str | None = "1e31f3f4b909"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COST = "buy_in * (1 + rebuys + reentries) + addon_cost"
_WIN = "prize + bounty"


def upgrade() -> None:
    # index depends on profit_base — drop before dropping the column
    op.drop_index("ix_tournaments_user_profit", table_name="tournaments")
    op.execute("ALTER TABLE tournaments DROP COLUMN profit_native")
    op.execute("ALTER TABLE tournaments DROP COLUMN profit_base")

    op.execute(
        "ALTER TABLE tournaments ADD COLUMN bounty NUMERIC(14,2) "
        "NOT NULL DEFAULT 0"
    )
    op.execute(
        f"ALTER TABLE tournaments ADD COLUMN total_winnings NUMERIC(16,2) "
        f"GENERATED ALWAYS AS ({_WIN}) STORED"
    )
    op.execute(
        f"ALTER TABLE tournaments ADD COLUMN profit_native NUMERIC(16,2) "
        f"GENERATED ALWAYS AS (({_WIN}) - ({_COST})) STORED"
    )
    op.execute(
        f"ALTER TABLE tournaments ADD COLUMN profit_base NUMERIC(18,2) "
        f"GENERATED ALWAYS AS ((({_WIN}) - ({_COST})) * fx_rate_to_base) STORED"
    )
    op.create_index(
        "ix_tournaments_user_profit",
        "tournaments",
        ["user_id", "profit_base"],
    )


def downgrade() -> None:
    op.drop_index("ix_tournaments_user_profit", table_name="tournaments")
    op.execute("ALTER TABLE tournaments DROP COLUMN profit_base")
    op.execute("ALTER TABLE tournaments DROP COLUMN profit_native")
    op.execute("ALTER TABLE tournaments DROP COLUMN total_winnings")
    op.execute("ALTER TABLE tournaments DROP COLUMN bounty")

    op.execute(
        f"ALTER TABLE tournaments ADD COLUMN profit_native NUMERIC(14,2) "
        f"GENERATED ALWAYS AS (prize - ({_COST})) STORED"
    )
    op.execute(
        f"ALTER TABLE tournaments ADD COLUMN profit_base NUMERIC(16,2) "
        f"GENERATED ALWAYS AS ((prize - ({_COST})) * fx_rate_to_base) STORED"
    )
    op.create_index(
        "ix_tournaments_user_profit",
        "tournaments",
        ["user_id", "profit_base"],
    )
