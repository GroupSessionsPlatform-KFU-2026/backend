"""add enums for room and pomodoro

Revision ID: 0a5b9ea5a834
Revises: 7fa7989f06af
Create Date: 2026-03-29 11:29:45.408121

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0a5b9ea5a834'
down_revision: Union[str, Sequence[str], None] = '7fa7989f06af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


pomodoro_phase_enum = postgresql.ENUM(
    'work',
    'short_break',
    'long_break',
    name='pomodorophase',
)

room_status_enum = postgresql.ENUM(
    'active',
    'ended',
    name='roomstatus',
)


def upgrade() -> None:
    pomodoro_phase_enum.create(op.get_bind(), checkfirst=True)
    room_status_enum.create(op.get_bind(), checkfirst=True)

    op.execute(
        """
        ALTER TABLE pomodoro_session
        ALTER COLUMN current_phase TYPE pomodorophase
        USING lower(current_phase)::pomodorophase
        """
    )

    op.execute(
        """
        ALTER TABLE room
        ALTER COLUMN status TYPE roomstatus
        USING lower(status)::roomstatus
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE pomodoro_session
        ALTER COLUMN current_phase TYPE VARCHAR
        USING current_phase::text
        """
    )

    op.execute(
        """
        ALTER TABLE room
        ALTER COLUMN status TYPE VARCHAR
        USING status::text
        """
    )

    room_status_enum.drop(op.get_bind(), checkfirst=True)
    pomodoro_phase_enum.drop(op.get_bind(), checkfirst=True)
