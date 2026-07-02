"""0013 style signals — unified activity log for personalization

Revision ID: 0013_style_signals
Revises: 0012_marketplace_v1
Create Date: 2026-07-02 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0013_style_signals"
down_revision: Union[str, None] = "0012_marketplace_v1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "style_signals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("top_id", sa.Integer(), nullable=True),
        sa.Column("bottom_id", sa.Integer(), nullable=True),
        sa.Column("shoes_id", sa.Integer(), nullable=True),
        sa.Column("outerwear_id", sa.Integer(), nullable=True),
        sa.Column("swap_slot", sa.String(length=16), nullable=True),
        sa.Column("replaced_item_id", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.String(length=64), nullable=True),
        sa.Column("post_id", sa.Integer(), nullable=True),
        sa.Column("occasion", sa.String(), nullable=True),
        sa.Column("weather_tag", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["top_id"], ["clothing_items.id"]),
        sa.ForeignKeyConstraint(["bottom_id"], ["clothing_items.id"]),
        sa.ForeignKeyConstraint(["shoes_id"], ["clothing_items.id"]),
        sa.ForeignKeyConstraint(["outerwear_id"], ["clothing_items.id"]),
        sa.ForeignKeyConstraint(["replaced_item_id"], ["clothing_items.id"]),
        sa.ForeignKeyConstraint(["post_id"], ["social_posts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_style_signals_id"), "style_signals", ["id"], unique=False)
    op.create_index(op.f("ix_style_signals_user_id"), "style_signals", ["user_id"], unique=False)
    op.create_index(op.f("ix_style_signals_event_type"), "style_signals", ["event_type"], unique=False)

    op.execute(
        """
        INSERT INTO style_signals (
            user_id, event_type, top_id, bottom_id, shoes_id, outerwear_id,
            occasion, weather_tag, created_at
        )
        SELECT
            user_id,
            CASE signal
                WHEN -3 THEN 'dislike'
                WHEN 2 THEN 'wore'
                WHEN 3 THEN 'like'
                ELSE 'like'
            END,
            top_id, bottom_id, shoes_id, outerwear_id,
            occasion, weather_tag, created_at
        FROM outfit_feedback
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_style_signals_event_type"), table_name="style_signals")
    op.drop_index(op.f("ix_style_signals_user_id"), table_name="style_signals")
    op.drop_index(op.f("ix_style_signals_id"), table_name="style_signals")
    op.drop_table("style_signals")
