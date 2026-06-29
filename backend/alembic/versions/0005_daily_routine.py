"""daily routine preferences per user

Revision ID: 0005_daily_routine
Revises: 0004_wear_laundry_tracking
Create Date: 2026-06-29 01:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_daily_routine"
down_revision: Union[str, None] = "0004_wear_laundry_tracking"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_routines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("wake_time", sa.String(), nullable=False, server_default="07:00"),
        sa.Column("weekday_activities", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("weekend_activities", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("gym_days", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("default_weather_tag", sa.String(), nullable=True),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_daily_routines_id"), "daily_routines", ["id"], unique=False)
    op.create_index(op.f("ix_daily_routines_user_id"), "daily_routines", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_daily_routines_user_id"), table_name="daily_routines")
    op.drop_index(op.f("ix_daily_routines_id"), table_name="daily_routines")
    op.drop_table("daily_routines")
