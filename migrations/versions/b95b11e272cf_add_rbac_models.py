"""add rbac models

Revision ID: b95b11e272cf
Revises: f1146c74a873
Create Date: 2026-04-09 15:28:01.617460

"""

import sqlalchemy as sa
import sqlmodel  # NEW
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b95b11e272cf'
down_revision = 'f1146c74a873'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'permission',
        sa.Column('subject', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('action', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('subject', 'action', name='uq_permission_subject_action'),
    )

    op.create_table(
        'role',
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_role_name'),
    )

    op.create_table(
        'role_permission',
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.Column('permission_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.id']),
        sa.ForeignKeyConstraint(['role_id'], ['role.id']),
        sa.PrimaryKeyConstraint('role_id', 'permission_id'),
    )

    op.create_table(
        'user_role',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('role_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id']),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('user_id', 'role_id'),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_table('user_role')
    op.drop_table('role_permission')
    op.drop_table('role')
    op.drop_table('permission')
