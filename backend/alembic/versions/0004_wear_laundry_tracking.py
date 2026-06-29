"""wear and laundry tracking on clothing items

Adds counters/timestamps that power the wear→laundry loop: wears since last wash,
last worn/washed timestamps, and a per-item wear-limit override.

Revision ID: 0004_wear_laundry_tracking
Revises: 0003_multi_value_context
Create Date: 2026-06-29 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_wear_laundry_tracking"
down_revision: Union[str, None] = "0003_multi_value_context"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clothing_items",
        sa.Column("wears_since_wash", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "clothing_items", sa.Column("last_worn_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "clothing_items", sa.Column("last_washed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("clothing_items", sa.Column("wear_limit", sa.Integer(), nullable=True))


def downgrade() -> None:
    for column in ("wear_limit", "last_washed_at", "last_worn_at", "wears_since_wash"):
        op.drop_column("clothing_items", column)
