"""update refresh sessions token identifiers

Revision ID: a7d308e9b3c0
Revises: b95b11e272cf
Create Date: 2026-04-11 12:37:02.672793

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7d308e9b3c0'
down_revision: Union[str, Sequence[str], None] = 'b95b11e272cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('DELETE FROM refresh_sessions')

    op.add_column(
        'refresh_sessions',
        sa.Column('refresh_jti', sa.Uuid(), nullable=False),
    )
    op.add_column(
        'refresh_sessions',
        sa.Column('access_jti', sa.Uuid(), nullable=False),
    )

    op.create_index(
        op.f('ix_refresh_sessions_refresh_jti'),
        'refresh_sessions',
        ['refresh_jti'],
        unique=True,
    )
    op.create_index(
        op.f('ix_refresh_sessions_access_jti'),
        'refresh_sessions',
        ['access_jti'],
        unique=True,
    )

    op.drop_index(op.f('ix_refresh_sessions_jti'), table_name='refresh_sessions')
    op.drop_column('refresh_sessions', 'jti')


def downgrade() -> None:
    op.add_column(
        'refresh_sessions',
        sa.Column('jti', sa.String(length=255), nullable=False),
    )

    op.create_index(
        op.f('ix_refresh_sessions_jti'),
        'refresh_sessions',
        ['jti'],
        unique=True,
    )

    op.drop_index(
        op.f('ix_refresh_sessions_access_jti'),
        table_name='refresh_sessions',
    )
    op.drop_index(
        op.f('ix_refresh_sessions_refresh_jti'),
        table_name='refresh_sessions',
    )

    op.drop_column('refresh_sessions', 'access_jti')
    op.drop_column('refresh_sessions', 'refresh_jti')
