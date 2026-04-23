"""add is_verified to user

Revision ID: e5bea7293608
Revises: 3e8ba93ed850
Create Date: 2026-04-23 17:20:58.159830

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e5bea7293608'
down_revision = '3e8ba93ed850'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'user',
        sa.Column(
            'is_verified',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.alter_column('user', 'is_verified', server_default=None)


def downgrade() -> None:
    op.drop_column('user', 'is_verified')
