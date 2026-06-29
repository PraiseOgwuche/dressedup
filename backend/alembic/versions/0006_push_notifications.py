"""push tokens and routine timezone for morning notifications

Revision ID: 0006_push_notifications
Revises: 0005_daily_routine
Create Date: 2026-06-29 02:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_push_notifications"
down_revision: Union[str, None] = "0005_daily_routine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("daily_routines", sa.Column("timezone", sa.String(), nullable=False, server_default="UTC"))
    op.add_column("daily_routines", sa.Column("last_morning_push_at", sa.Date(), nullable=True))

    op.create_table(
        "push_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("platform", sa.String(), nullable=True),
        sa.Column("timezone", sa.String(), nullable=False, server_default="UTC"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token", name="uq_push_tokens_token"),
    )
    op.create_index(op.f("ix_push_tokens_id"), "push_tokens", ["id"], unique=False)
    op.create_index(op.f("ix_push_tokens_user_id"), "push_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_push_tokens_user_id"), table_name="push_tokens")
    op.drop_index(op.f("ix_push_tokens_id"), table_name="push_tokens")
    op.drop_table("push_tokens")
    op.drop_column("daily_routines", "last_morning_push_at")
    op.drop_column("daily_routines", "timezone")
