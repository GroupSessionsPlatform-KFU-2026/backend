"""restore refresh sessions table

Revision ID: 83ae5d5b1779
Revises: b95b11e272cf
Create Date: 2026-04-09 21:31:15.097741

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '83ae5d5b1779'
down_revision = 'b95b11e272cf'
branch_labels = None
depends_on = None


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
        sa.ForeignKeyConstraint(
            ['user_id'], ['user.id'], name=op.f('refresh_sessions_user_id_fkey')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('refresh_sessions_pkey')),
        sa.UniqueConstraint(
            'jti',
            name=op.f('refresh_sessions_jti_key'),
            postgresql_include=[],
            postgresql_nulls_not_distinct=False,
        ),
    )
    op.create_index(
        op.f('ix_refresh_sessions_user_id'),
        'refresh_sessions',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_refresh_sessions_jti'),
        'refresh_sessions',
        ['jti'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_refresh_sessions_jti'), table_name='refresh_sessions')
    op.drop_index(op.f('ix_refresh_sessions_user_id'), table_name='refresh_sessions')
    op.drop_table('refresh_sessions')
