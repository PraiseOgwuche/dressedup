"""multi-value occasion and weather_tag on clothing items

Converts clothing_items.occasion and weather_tag from a single string to a JSON
list ("pick all that apply"). Existing scalar values are wrapped into a 1-element
array; empty strings become NULL. Postgres-specific (the app's database).

Revision ID: 0003_multi_value_context
Revises: 0002_rich_clothing_attributes
Create Date: 2026-06-29 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0003_multi_value_context"
down_revision: Union[str, None] = "0002_rich_clothing_attributes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_clothing_items_occasion"), table_name="clothing_items")
    op.drop_index(op.f("ix_clothing_items_weather_tag"), table_name="clothing_items")

    for column in ("occasion", "weather_tag"):
        op.execute(
            f"""
            ALTER TABLE clothing_items
            ALTER COLUMN {column} TYPE jsonb
            USING (
                CASE
                    WHEN {column} IS NULL OR {column} = '' THEN NULL
                    ELSE to_jsonb(ARRAY[{column}])
                END
            )
            """
        )


def downgrade() -> None:
    # Collapse the list back to its first element (best-effort).
    for column in ("occasion", "weather_tag"):
        op.execute(
            f"""
            ALTER TABLE clothing_items
            ALTER COLUMN {column} TYPE varchar
            USING (
                CASE
                    WHEN {column} IS NULL OR jsonb_array_length({column}) = 0 THEN NULL
                    ELSE ({column} ->> 0)
                END
            )
            """
        )

    op.create_index(
        op.f("ix_clothing_items_occasion"), "clothing_items", ["occasion"], unique=False
    )
    op.create_index(
        op.f("ix_clothing_items_weather_tag"), "clothing_items", ["weather_tag"], unique=False
    )
