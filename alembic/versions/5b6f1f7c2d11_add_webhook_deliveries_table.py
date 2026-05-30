"""add webhook deliveries table

Revision ID: 5b6f1f7c2d11
Revises: 1d9b3e7a4f21
Create Date: 2026-05-30 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5b6f1f7c2d11"
down_revision: Union[str, Sequence[str], None] = "1d9b3e7a4f21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("next_retry_at", sa.DateTime(), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("replayed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'processed', 'failed', 'dead_letter', 'replayed')",
            name="ck_webhook_delivery_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id"),
    )
    op.create_index(op.f("ix_webhook_deliveries_id"), "webhook_deliveries", ["id"], unique=False)
    op.create_index(op.f("ix_webhook_deliveries_provider"), "webhook_deliveries", ["provider"], unique=False)
    op.create_index(op.f("ix_webhook_deliveries_event_id"), "webhook_deliveries", ["event_id"], unique=True)
    op.create_index(op.f("ix_webhook_deliveries_event_type"), "webhook_deliveries", ["event_type"], unique=False)
    op.create_index(op.f("ix_webhook_deliveries_status"), "webhook_deliveries", ["status"], unique=False)
    op.create_index(
        op.f("ix_webhook_deliveries_next_retry_at"),
        "webhook_deliveries",
        ["next_retry_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_webhook_deliveries_next_retry_at"), table_name="webhook_deliveries")
    op.drop_index(op.f("ix_webhook_deliveries_status"), table_name="webhook_deliveries")
    op.drop_index(op.f("ix_webhook_deliveries_event_type"), table_name="webhook_deliveries")
    op.drop_index(op.f("ix_webhook_deliveries_event_id"), table_name="webhook_deliveries")
    op.drop_index(op.f("ix_webhook_deliveries_provider"), table_name="webhook_deliveries")
    op.drop_index(op.f("ix_webhook_deliveries_id"), table_name="webhook_deliveries")
    op.drop_table("webhook_deliveries")
