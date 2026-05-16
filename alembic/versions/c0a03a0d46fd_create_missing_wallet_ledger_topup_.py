"""create missing wallet ledger topup tables

Revision ID: c0a03a0d46fd
Revises: 90f8f98a1912
Create Date: 2026-05-16 09:50:36.995805

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0a03a0d46fd'
down_revision: Union[str, Sequence[str], None] = '90f8f98a1912'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'wallets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('balance', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('auto_top_up_enabled', sa.Boolean(), nullable=False),
        sa.Column('auto_top_up_amount', sa.Integer(), nullable=False),
        sa.Column('auto_top_up_threshold', sa.Integer(), nullable=False),
        sa.Column('auto_top_up_daily_limit', sa.Integer(), nullable=False),
        sa.Column('auto_top_up_monthly', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_wallets_id'), 'wallets', ['id'], unique=False)
    op.create_index(op.f('ix_wallets_user_id'), 'wallets', ['user_id'], unique=True)

    op.create_table(
        'ledger',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('delta', sa.Integer(), nullable=False),
        sa.Column('entry_type', sa.String(), nullable=False),
        sa.Column('reference', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('delta <> 0', name='ck_ledger_delta_nonzero'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ledger_id'), 'ledger', ['id'], unique=False)
    op.create_index(op.f('ix_ledger_user_id'), 'ledger', ['user_id'], unique=False)

    op.create_table(
        'topup_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('credits', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('idempotency_key', sa.String(), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('initiated', 'paid', 'failed')", name='ck_topup_attempt_status'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key'),
    )
    op.create_index(op.f('ix_topup_attempts_id'), 'topup_attempts', ['id'], unique=False)
    op.create_index(op.f('ix_topup_attempts_idempotency_key'), 'topup_attempts', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_topup_attempts_status'), 'topup_attempts', ['status'], unique=False)
    op.create_index(op.f('ix_topup_attempts_stripe_payment_intent_id'), 'topup_attempts', ['stripe_payment_intent_id'], unique=False)
    op.create_index(op.f('ix_topup_attempts_user_id'), 'topup_attempts', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_topup_attempts_user_id'), table_name='topup_attempts')
    op.drop_index(op.f('ix_topup_attempts_stripe_payment_intent_id'), table_name='topup_attempts')
    op.drop_index(op.f('ix_topup_attempts_status'), table_name='topup_attempts')
    op.drop_index(op.f('ix_topup_attempts_idempotency_key'), table_name='topup_attempts')
    op.drop_index(op.f('ix_topup_attempts_id'), table_name='topup_attempts')
    op.drop_table('topup_attempts')

    op.drop_index(op.f('ix_ledger_user_id'), table_name='ledger')
    op.drop_index(op.f('ix_ledger_id'), table_name='ledger')
    op.drop_table('ledger')

    op.drop_index(op.f('ix_wallets_user_id'), table_name='wallets')
    op.drop_index(op.f('ix_wallets_id'), table_name='wallets')
    op.drop_table('wallets')
