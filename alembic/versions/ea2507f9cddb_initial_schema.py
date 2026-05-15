"""initial schema

Revision ID: ea2507f9cddb
Revises: 
Create Date: 2026-04-23 22:52:11.045507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea2507f9cddb'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # Create accounts first.
    if 'accounts' not in existing_tables:
        op.create_table('accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_accounts_id'), 'accounts', ['id'], unique=False)
        op.create_index(op.f('ix_accounts_name'), 'accounts', ['name'], unique=True)

    if 'users' in existing_tables:
        user_columns = {col["name"] for col in inspector.get_columns("users")}

        # Add account_id as nullable first so we can backfill existing users.
        if 'account_id' not in user_columns:
            op.add_column('users', sa.Column('account_id', sa.Integer(), nullable=True))
        if 'api_key' not in user_columns:
            op.add_column('users', sa.Column('api_key', sa.String(), nullable=True))

        # Backfill one account per existing user, then attach users to those accounts.
        op.execute(
            sa.text(
                """
                INSERT INTO accounts (name, created_at)
                SELECT 'legacy_user_' || id::text, NOW()
                FROM users
                WHERE NOT EXISTS (
                    SELECT 1 FROM accounts a WHERE a.name = 'legacy_user_' || users.id::text
                )
                """
            )
        )
        op.execute(
            sa.text(
                """
                UPDATE users u
                SET account_id = a.id
                FROM accounts a
                WHERE a.name = 'legacy_user_' || u.id::text
                  AND u.account_id IS NULL
                """
            )
        )

        # Enforce non-null only after successful backfill.
        op.alter_column('users', 'account_id', nullable=False)
    else:
        # Fresh database bootstrap path (e.g., new Render Postgres).
        op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('api_key', sa.String(), nullable=True),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name='fk_users_account_id_accounts', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('stripe_customer_id'),
        sa.UniqueConstraint('username')
        )

    op.create_index(op.f('ix_users_account_id'), 'users', ['account_id'], unique=False)
    op.create_index(op.f('ix_users_api_key'), 'users', ['api_key'], unique=True)
    if 'users' in existing_tables:
        op.create_foreign_key(
            'fk_users_account_id_accounts',
            'users',
            'accounts',
            ['account_id'],
            ['id'],
            ondelete='CASCADE',
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_users_account_id_accounts', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_api_key'), table_name='users')
    op.drop_index(op.f('ix_users_account_id'), table_name='users')
    op.drop_column('users', 'api_key')
    op.drop_column('users', 'account_id')
    op.drop_index(op.f('ix_accounts_name'), table_name='accounts')
    op.drop_index(op.f('ix_accounts_id'), table_name='accounts')
    op.drop_table('accounts')
