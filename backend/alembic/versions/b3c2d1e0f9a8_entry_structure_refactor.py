"""replace entry_structure with tournament_type and chip-purchase flags

Revision ID: b3c2d1e0f9a8
Revises: a2b1c0d4e5f6
Create Date: 2026-06-29

Entry policy was wrongly modeled as a single exclusive value. Rebuy / re-entry /
add-on are independent and combine freely (freezeout = none of them), and
satellite/shootout are an orthogonal tournament *type*. Replace the single
`entry_structure` column accordingly. No data backfill (empty tables).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3c2d1e0f9a8"
down_revision: str | None = "a2b1c0d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tournaments",
        sa.Column(
            "tournament_type",
            sa.String(length=12),
            nullable=False,
            server_default="normal",
        ),
    )
    op.create_check_constraint(
        "ck_tour_tournament_type",
        "tournaments",
        "tournament_type IN ('normal', 'satellite', 'shootout')",
    )
    for flag in ("allows_rebuy", "allows_reentry", "allows_addon"):
        op.add_column(
            "tournaments",
            sa.Column(
                flag, sa.Boolean(), nullable=False, server_default=sa.text("false")
            ),
        )
    # drop the old single-value column and its check
    op.drop_constraint("ck_tour_entry_structure", "tournaments", type_="check")
    op.drop_column("tournaments", "entry_structure")


def downgrade() -> None:
    op.add_column(
        "tournaments",
        sa.Column(
            "entry_structure",
            sa.String(length=12),
            nullable=False,
            server_default="freezeout",
        ),
    )
    op.create_check_constraint(
        "ck_tour_entry_structure",
        "tournaments",
        "entry_structure IN "
        "('freezeout', 'rebuy', 'reentry', 'satellite', 'shootout')",
    )
    op.drop_column("tournaments", "allows_addon")
    op.drop_column("tournaments", "allows_reentry")
    op.drop_column("tournaments", "allows_rebuy")
    op.drop_constraint("ck_tour_tournament_type", "tournaments", type_="check")
    op.drop_column("tournaments", "tournament_type")
