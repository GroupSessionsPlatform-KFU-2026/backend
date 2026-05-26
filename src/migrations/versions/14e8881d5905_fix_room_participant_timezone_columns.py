"""fix room_participant timezone columns

Revision ID: 14e8881d5905
Revises: a7d308e9b3c0
Create Date: 2026-04-16 00:16:32.744823
"""

from alembic import op
from sqlalchemy.dialects import postgresql

revision = '14e8881d5905'
down_revision = 'a7d308e9b3c0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'room_participant',
        'joined_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=True,
        postgresql_using="joined_at AT TIME ZONE 'UTC'",
    )
    op.alter_column(
        'room_participant',
        'left_at',
        existing_type=postgresql.TIMESTAMP(),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=True,
        postgresql_using="left_at AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        'room_participant',
        'left_at',
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
    op.alter_column(
        'room_participant',
        'joined_at',
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
