"""marketplace — peer sell/gift listings

Revision ID: 0012_marketplace_v1
Revises: 0011_feed_v2
Create Date: 2026-07-02 14:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0012_marketplace_v1"
down_revision: Union[str, None] = "0011_feed_v2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "closet_listings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("clothing_item_id", sa.Integer(), nullable=False),
        sa.Column("listing_type", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_cents", sa.Integer(), nullable=True),
        sa.Column("condition", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["clothing_item_id"], ["clothing_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_closet_listings_id"), "closet_listings", ["id"], unique=False)
    op.create_index(op.f("ix_closet_listings_user_id"), "closet_listings", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_closet_listings_clothing_item_id"), "closet_listings", ["clothing_item_id"], unique=False
    )
    op.create_index(op.f("ix_closet_listings_status"), "closet_listings", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_closet_listings_status"), table_name="closet_listings")
    op.drop_index(op.f("ix_closet_listings_clothing_item_id"), table_name="closet_listings")
    op.drop_index(op.f("ix_closet_listings_user_id"), table_name="closet_listings")
    op.drop_index(op.f("ix_closet_listings_id"), table_name="closet_listings")
    op.drop_table("closet_listings")
