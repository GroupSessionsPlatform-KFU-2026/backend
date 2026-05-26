"""create refresh sessions table

Revision ID: f0d9cf79f577
Revises: 0cbe64b17e41
Create Date: 2026-04-07 00:28:44.262641

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f0d9cf79f577'
down_revision: Union[str, Sequence[str], None] = '0cbe64b17e41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'refresh_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('jti', sa.String(length=255), nullable=False),
        sa.Column('expires_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            'is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')
        ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jti'),
    )
    op.create_index(
        op.f('ix_refresh_sessions_user_id'),
        'refresh_sessions',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_refresh_sessions_jti'), 'refresh_sessions', ['jti'], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_refresh_sessions_jti'), table_name='refresh_sessions')
    op.drop_index(op.f('ix_refresh_sessions_user_id'), table_name='refresh_sessions')
    op.drop_table('refresh_sessions')
