"""0014 user feed state — activity read tracking

Revision ID: 0014_user_feed_state
Revises: 0013_style_signals
Create Date: 2026-07-09 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0014_user_feed_state"
down_revision: Union[str, None] = "0013_style_signals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_feed_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_feed_state_id"), "user_feed_state", ["id"], unique=False)
    op.create_index(op.f("ix_user_feed_state_user_id"), "user_feed_state", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_feed_state_user_id"), table_name="user_feed_state")
    op.drop_index(op.f("ix_user_feed_state_id"), table_name="user_feed_state")
    op.drop_table("user_feed_state")
