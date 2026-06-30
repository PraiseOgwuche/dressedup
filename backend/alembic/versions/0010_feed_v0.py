"""feed v0 — outfit posts and likes

Revision ID: 0010_feed_v0
Revises: 0009_trip_dates
Create Date: 2026-06-29 20:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010_feed_v0"
down_revision: Union[str, None] = "0009_trip_dates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("social_posts", sa.Column("top_id", sa.Integer(), nullable=True))
    op.add_column("social_posts", sa.Column("bottom_id", sa.Integer(), nullable=True))
    op.add_column("social_posts", sa.Column("shoes_id", sa.Integer(), nullable=True))
    op.add_column("social_posts", sa.Column("outerwear_id", sa.Integer(), nullable=True))
    op.add_column("social_posts", sa.Column("photo_url", sa.String(length=500), nullable=True))
    op.create_foreign_key(
        "fk_social_posts_top_id",
        "social_posts",
        "clothing_items",
        ["top_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_social_posts_bottom_id",
        "social_posts",
        "clothing_items",
        ["bottom_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_social_posts_shoes_id",
        "social_posts",
        "clothing_items",
        ["shoes_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_social_posts_outerwear_id",
        "social_posts",
        "clothing_items",
        ["outerwear_id"],
        ["id"],
    )
    op.alter_column("social_posts", "caption", existing_type=sa.Text(), nullable=True)

    op.create_table(
        "social_post_likes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["post_id"], ["social_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_social_post_likes_post_user"),
    )
    op.create_index(op.f("ix_social_post_likes_id"), "social_post_likes", ["id"], unique=False)
    op.create_index(op.f("ix_social_post_likes_post_id"), "social_post_likes", ["post_id"], unique=False)
    op.create_index(op.f("ix_social_post_likes_user_id"), "social_post_likes", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_social_post_likes_user_id"), table_name="social_post_likes")
    op.drop_index(op.f("ix_social_post_likes_post_id"), table_name="social_post_likes")
    op.drop_index(op.f("ix_social_post_likes_id"), table_name="social_post_likes")
    op.drop_table("social_post_likes")

    op.alter_column("social_posts", "caption", existing_type=sa.Text(), nullable=False)
    op.drop_constraint("fk_social_posts_outerwear_id", "social_posts", type_="foreignkey")
    op.drop_constraint("fk_social_posts_shoes_id", "social_posts", type_="foreignkey")
    op.drop_constraint("fk_social_posts_bottom_id", "social_posts", type_="foreignkey")
    op.drop_constraint("fk_social_posts_top_id", "social_posts", type_="foreignkey")
    op.drop_column("social_posts", "photo_url")
    op.drop_column("social_posts", "outerwear_id")
    op.drop_column("social_posts", "shoes_id")
    op.drop_column("social_posts", "bottom_id")
    op.drop_column("social_posts", "top_id")
