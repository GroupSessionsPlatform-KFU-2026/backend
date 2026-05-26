"""add board anonymity flags

Revision ID: 8c2d54f9a7b1
Revises: 4b7f2a9c1d6e
Create Date: 2026-05-18 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '8c2d54f9a7b1'
down_revision = '4b7f2a9c1d6e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'board_element',
        sa.Column(
            'is_anonymous',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        'board_element_comment',
        sa.Column(
            'is_anonymous',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column('board_element', 'is_anonymous', server_default=None)
    op.alter_column('board_element_comment', 'is_anonymous', server_default=None)


def downgrade() -> None:
    op.drop_column('board_element_comment', 'is_anonymous')
    op.drop_column('board_element', 'is_anonymous')
