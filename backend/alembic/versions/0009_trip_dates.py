"""trip start and end dates for weather-aware packing

Revision ID: 0009_trip_dates
Revises: 0008_outfit_feedback
Create Date: 2026-06-29 18:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0009_trip_dates"
down_revision: Union[str, None] = "0008_outfit_feedback"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("trip_plans", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("trip_plans", sa.Column("end_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("trip_plans", "end_date")
    op.drop_column("trip_plans", "start_date")
