"""rich clothing attributes for AI ingestion

Revision ID: 0002_rich_clothing_attributes
Revises: 0001_initial_domain_models
Create Date: 2026-06-29 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_rich_clothing_attributes"
down_revision: Union[str, None] = "0001_initial_domain_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clothing_items", sa.Column("product_name", sa.String(), nullable=True))
    op.add_column("clothing_items", sa.Column("size", sa.String(), nullable=True))
    op.add_column("clothing_items", sa.Column("subcategory", sa.String(), nullable=True))
    op.add_column("clothing_items", sa.Column("color_hex", sa.String(), nullable=True))
    op.add_column("clothing_items", sa.Column("pattern", sa.String(), nullable=True))
    op.add_column("clothing_items", sa.Column("material", sa.String(), nullable=True))
    op.add_column("clothing_items", sa.Column("formality", sa.String(), nullable=True))
    op.add_column("clothing_items", sa.Column("seasons", sa.JSON(), nullable=True))
    op.add_column("clothing_items", sa.Column("image_url", sa.String(), nullable=True))
    op.add_column("clothing_items", sa.Column("thumbnail_url", sa.String(), nullable=True))
    op.add_column(
        "clothing_items",
        sa.Column("source", sa.String(), nullable=False, server_default="manual"),
    )
    op.add_column("clothing_items", sa.Column("confidence", sa.JSON(), nullable=True))
    op.add_column(
        "clothing_items",
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("clothing_items", sa.Column("ai_metadata", sa.JSON(), nullable=True))

    op.create_index(
        op.f("ix_clothing_items_subcategory"), "clothing_items", ["subcategory"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_clothing_items_subcategory"), table_name="clothing_items")
    for column in (
        "ai_metadata",
        "needs_review",
        "confidence",
        "source",
        "thumbnail_url",
        "image_url",
        "seasons",
        "formality",
        "material",
        "pattern",
        "color_hex",
        "subcategory",
        "size",
        "product_name",
    ):
        op.drop_column("clothing_items", column)
