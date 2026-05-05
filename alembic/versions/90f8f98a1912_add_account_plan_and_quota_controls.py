"""add account plan and quota controls

Revision ID: 90f8f98a1912
Revises: 679a3d8d68c0
Create Date: 2026-05-05 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90f8f98a1912'
down_revision: Union[str, Sequence[str], None] = '679a3d8d68c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('accounts', sa.Column('plan_name', sa.String(), nullable=False, server_default='free'))
    op.add_column('accounts', sa.Column('monthly_credit_quota', sa.Integer(), nullable=False, server_default='10000'))
    op.add_column('accounts', sa.Column('period_spend_credits', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('accounts', sa.Column('period_started_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')))
    op.add_column('accounts', sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    op.drop_column('accounts', 'is_suspended')
    op.drop_column('accounts', 'period_started_at')
    op.drop_column('accounts', 'period_spend_credits')
    op.drop_column('accounts', 'monthly_credit_quota')
    op.drop_column('accounts', 'plan_name')
