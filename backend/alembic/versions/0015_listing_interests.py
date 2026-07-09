"""0015 listing interests — persist Pass it on interest list

Revision ID: 0015_listing_interests
Revises: 0014_user_feed_state
Create Date: 2026-07-09 14:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0015_listing_interests"
down_revision: Union[str, None] = "0014_user_feed_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "listing_interests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["listing_id"], ["closet_listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("listing_id", "user_id", name="uq_listing_interests_pair"),
    )
    op.create_index(op.f("ix_listing_interests_id"), "listing_interests", ["id"], unique=False)
    op.create_index(op.f("ix_listing_interests_listing_id"), "listing_interests", ["listing_id"], unique=False)
    op.create_index(op.f("ix_listing_interests_user_id"), "listing_interests", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_listing_interests_user_id"), table_name="listing_interests")
    op.drop_index(op.f("ix_listing_interests_listing_id"), table_name="listing_interests")
    op.drop_index(op.f("ix_listing_interests_id"), table_name="listing_interests")
    op.drop_table("listing_interests")
