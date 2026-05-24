"""fix user last_login_at timezone2

Revision ID: f1146c74a873
Revises: 2bdecc1a8807
Create Date: 2026-04-07 00:43:20.966154

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f1146c74a873'
down_revision = 'f0d9cf79f577'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'user',
        'last_login_at',
        existing_type=sa.TIMESTAMP(timezone=False),
        type_=sa.TIMESTAMP(timezone=True),
        existing_nullable=True,
        postgresql_using="last_login_at AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        'user',
        'last_login_at',
        existing_type=sa.TIMESTAMP(timezone=True),
        type_=sa.TIMESTAMP(timezone=False),
        existing_nullable=True,
        postgresql_using="last_login_at AT TIME ZONE 'UTC'",
    )
