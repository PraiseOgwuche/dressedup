"""0019 user avatar_url for Ready Player Me

Stores the exported .glb URL from Ready Player Me so Home can render the
user's personalized avatar.

Revision ID: 0019_user_avatar_url
Revises: 0018_dress_slot
Create Date: 2026-07-21 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0019_user_avatar_url"
down_revision: Union[str, None] = "0018_dress_slot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_url", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_url")
