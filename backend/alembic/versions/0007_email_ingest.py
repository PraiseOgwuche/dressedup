"""email ingest token and import logs

Revision ID: 0007_email_ingest
Revises: 0006_push_notifications
Create Date: 2026-06-29 12:00:00.000000
"""

import secrets
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007_email_ingest"
down_revision: Union[str, None] = "0006_push_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("ingest_token", sa.String(length=32), nullable=True))
    op.create_index(op.f("ix_users_ingest_token"), "users", ["ingest_token"], unique=True)

    connection = op.get_bind()
    users = connection.execute(sa.text("SELECT id FROM users WHERE ingest_token IS NULL")).fetchall()
    for (user_id,) in users:
        token = secrets.token_hex(8)
        connection.execute(
            sa.text("UPDATE users SET ingest_token = :token WHERE id = :id"),
            {"token": token, "id": user_id},
        )

    op.alter_column("users", "ingest_token", nullable=False)

    op.create_table(
        "email_ingest_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("sender", sa.String(), nullable=True),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("items_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attachments_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_ingest_logs_id"), "email_ingest_logs", ["id"], unique=False)
    op.create_index(op.f("ix_email_ingest_logs_user_id"), "email_ingest_logs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_email_ingest_logs_user_id"), table_name="email_ingest_logs")
    op.drop_index(op.f("ix_email_ingest_logs_id"), table_name="email_ingest_logs")
    op.drop_table("email_ingest_logs")
    op.drop_index(op.f("ix_users_ingest_token"), table_name="users")
    op.drop_column("users", "ingest_token")
