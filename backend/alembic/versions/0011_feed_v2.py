"""feed v2 — follows and comments

Revision ID: 0011_feed_v2
Revises: 0010_feed_v0
Create Date: 2026-07-02 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0011_feed_v2"
down_revision: Union[str, None] = "0010_feed_v0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_follows",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("follower_id", sa.Integer(), nullable=False),
        sa.Column("following_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["follower_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["following_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("follower_id", "following_id", name="uq_user_follows_pair"),
    )
    op.create_index(op.f("ix_user_follows_id"), "user_follows", ["id"], unique=False)
    op.create_index(op.f("ix_user_follows_follower_id"), "user_follows", ["follower_id"], unique=False)
    op.create_index(op.f("ix_user_follows_following_id"), "user_follows", ["following_id"], unique=False)

    op.create_table(
        "social_post_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["post_id"], ["social_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_social_post_comments_id"), "social_post_comments", ["id"], unique=False)
    op.create_index(op.f("ix_social_post_comments_post_id"), "social_post_comments", ["post_id"], unique=False)
    op.create_index(op.f("ix_social_post_comments_user_id"), "social_post_comments", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_social_post_comments_user_id"), table_name="social_post_comments")
    op.drop_index(op.f("ix_social_post_comments_post_id"), table_name="social_post_comments")
    op.drop_index(op.f("ix_social_post_comments_id"), table_name="social_post_comments")
    op.drop_table("social_post_comments")

    op.drop_index(op.f("ix_user_follows_following_id"), table_name="user_follows")
    op.drop_index(op.f("ix_user_follows_follower_id"), table_name="user_follows")
    op.drop_index(op.f("ix_user_follows_id"), table_name="user_follows")
    op.drop_table("user_follows")
