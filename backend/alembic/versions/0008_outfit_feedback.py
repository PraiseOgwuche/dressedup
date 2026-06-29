"""0008 outfit feedback for preference learning

Revision ID: 0008_outfit_feedback
Revises: 0007_email_ingest
Create Date: 2026-06-29 14:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008_outfit_feedback"
down_revision: Union[str, None] = "0007_email_ingest"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "outfit_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("top_id", sa.Integer(), nullable=True),
        sa.Column("bottom_id", sa.Integer(), nullable=True),
        sa.Column("shoes_id", sa.Integer(), nullable=True),
        sa.Column("outerwear_id", sa.Integer(), nullable=True),
        sa.Column("signal", sa.Integer(), nullable=False),
        sa.Column("occasion", sa.String(), nullable=True),
        sa.Column("weather_tag", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["top_id"], ["clothing_items.id"]),
        sa.ForeignKeyConstraint(["bottom_id"], ["clothing_items.id"]),
        sa.ForeignKeyConstraint(["shoes_id"], ["clothing_items.id"]),
        sa.ForeignKeyConstraint(["outerwear_id"], ["clothing_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_outfit_feedback_id"), "outfit_feedback", ["id"], unique=False)
    op.create_index(op.f("ix_outfit_feedback_user_id"), "outfit_feedback", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_outfit_feedback_user_id"), table_name="outfit_feedback")
    op.drop_index(op.f("ix_outfit_feedback_id"), table_name="outfit_feedback")
    op.drop_table("outfit_feedback")
