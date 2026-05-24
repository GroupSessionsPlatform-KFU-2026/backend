"""add mvp backend fields

Revision ID: 4b7f2a9c1d6e
Revises: e5bea7293608
Create Date: 2026-05-14 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4b7f2a9c1d6e'
down_revision = 'e5bea7293608'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'project',
        sa.Column('deadline', sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        'project',
        sa.Column(
            'required_roles',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.alter_column('project', 'required_roles', server_default=None)

    op.execute("ALTER TYPE boardelementtype ADD VALUE IF NOT EXISTS 'question'")
    op.execute("ALTER TYPE boardelementtype ADD VALUE IF NOT EXISTS 'decision'")


def downgrade() -> None:
    op.execute(
        """
        UPDATE board_element
        SET element_type = 'marker'
        WHERE element_type::text IN ('question', 'decision')
        """
    )
    op.execute('ALTER TYPE boardelementtype RENAME TO boardelementtype_old')

    board_element_type = postgresql.ENUM(
        'brush',
        'eraser',
        'marker',
        'shape',
        'text',
        name='boardelementtype',
    )
    board_element_type.create(op.get_bind(), checkfirst=True)

    op.execute(
        """
        ALTER TABLE board_element
        ALTER COLUMN element_type TYPE boardelementtype
        USING element_type::text::boardelementtype
        """
    )
    op.execute('DROP TYPE boardelementtype_old')

    op.drop_column('project', 'required_roles')
    op.drop_column('project', 'deadline')
