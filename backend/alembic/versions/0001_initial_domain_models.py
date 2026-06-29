"""initial domain models

Revision ID: 0001_initial_domain_models
Revises:
Create Date: 2026-04-04 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_domain_models"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("is_premium", sa.Boolean(), nullable=True),
        sa.Column("premium_trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "clothing_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("color", sa.String(), nullable=True),
        sa.Column("brand", sa.String(), nullable=True),
        sa.Column("occasion", sa.String(), nullable=True),
        sa.Column("weather_tag", sa.String(), nullable=True),
        sa.Column("is_clean", sa.Boolean(), nullable=True),
        sa.Column("times_worn", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clothing_items_category"), "clothing_items", ["category"], unique=False)
    op.create_index(op.f("ix_clothing_items_id"), "clothing_items", ["id"], unique=False)
    op.create_index(op.f("ix_clothing_items_occasion"), "clothing_items", ["occasion"], unique=False)
    op.create_index(op.f("ix_clothing_items_user_id"), "clothing_items", ["user_id"], unique=False)
    op.create_index(op.f("ix_clothing_items_weather_tag"), "clothing_items", ["weather_tag"], unique=False)

    op.create_table(
        "social_posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("look_name", sa.String(), nullable=True),
        sa.Column("occasion", sa.String(), nullable=True),
        sa.Column("reactions_count", sa.Integer(), nullable=True),
        sa.Column("comments_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_social_posts_id"), "social_posts", ["id"], unique=False)
    op.create_index(op.f("ix_social_posts_user_id"), "social_posts", ["user_id"], unique=False)

    op.create_table(
        "trip_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("destination", sa.String(), nullable=False),
        sa.Column("weather_tag", sa.String(), nullable=True),
        sa.Column("days", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trip_plans_id"), "trip_plans", ["id"], unique=False)
    op.create_index(op.f("ix_trip_plans_user_id"), "trip_plans", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_trip_plans_user_id"), table_name="trip_plans")
    op.drop_index(op.f("ix_trip_plans_id"), table_name="trip_plans")
    op.drop_table("trip_plans")
    op.drop_index(op.f("ix_social_posts_user_id"), table_name="social_posts")
    op.drop_index(op.f("ix_social_posts_id"), table_name="social_posts")
    op.drop_table("social_posts")
    op.drop_index(op.f("ix_clothing_items_weather_tag"), table_name="clothing_items")
    op.drop_index(op.f("ix_clothing_items_user_id"), table_name="clothing_items")
    op.drop_index(op.f("ix_clothing_items_occasion"), table_name="clothing_items")
    op.drop_index(op.f("ix_clothing_items_id"), table_name="clothing_items")
    op.drop_index(op.f("ix_clothing_items_category"), table_name="clothing_items")
    op.drop_table("clothing_items")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

