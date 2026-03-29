"""update pomodoro session model

Revision ID: ec0db1362d90
Revises: 0c3f945eb80f
Create Date: 2026-03-27 14:32:58.123503

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'ec0db1362d90'
down_revision = '0c3f945eb80f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    board_element_type = sa.Enum(
        'brush',
        'eraser',
        'marker',
        'shape',
        'text',
        name='boardelementtype',
    )
    board_element_type.create(op.get_bind(), checkfirst=True)

    op.alter_column(
        'board_element',
        'element_type',
        existing_type=sa.VARCHAR(),
        type_=board_element_type,
        existing_nullable=False,
        postgresql_using='element_type::boardelementtype',
    )

    op.drop_column('pomodoro_session', 'last_updated_at')


def downgrade() -> None:
    op.add_column(
        'pomodoro_session',
        sa.Column('last_updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
    )

    board_element_type = sa.Enum(
        'brush',
        'eraser',
        'marker',
        'shape',
        'text',
        name='boardelementtype',
    )

    op.alter_column(
        'board_element',
        'element_type',
        existing_type=board_element_type,
        type_=sa.VARCHAR(),
        existing_nullable=False,
        postgresql_using='element_type::text',
    )

    board_element_type.drop(op.get_bind(), checkfirst=True)
