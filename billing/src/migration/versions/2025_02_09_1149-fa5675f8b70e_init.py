"""init

Revision ID: fa5675f8b70e
Revises: 
Create Date: 2025-02-09 11:49:51.768075+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fa5675f8b70e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'refund',
        sa.Column(
            'payment_id',
            type_=sa.VARCHAR(),
            nullable=False,
        ),
        sa.Column('refund_id', sa.UUID(), nullable=False),
        sa.Column(
            'amount',
            existing_type=sa.INTEGER(),
            type_=sa.Numeric(precision=6, scale=2),
            nullable=False,
        ),
        sa.Column('status', sa.VARCHAR(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column(
            'created',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=True,
        ),
        sa.Column(
            'modified',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_refund_id'),
        'refund',
        ['id'],
        unique=True,
    )

    op.create_table('tariff',
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column(
        'price',
        sa.Numeric(precision=6, scale=2),
        nullable=False,
    ),
    sa.Column('currency', sa.String(length=3), nullable=True),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created',
              sa.DateTime(timezone=True),
              server_default=sa.text('now()'),
              nullable=True,
              ),
    sa.Column('modified', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        op.f('ix_tariff_id'),
        'tariff',
        ['id'],
        unique=True,
    )

    op.create_table('payment',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('tariff_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('payment_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column(
        'created',
        sa.DateTime(timezone=True),
        server_default=sa.text('now()'),
        nullable=True,
    ),
    sa.Column('modified', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(
        ['tariff_id'],
        ['tariff.id'],
        ondelete='SET NULL',
    ),
    sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_payment_id'), table_name='payment')
    op.drop_table('payment')
    op.drop_index(op.f('ix_tariff_id'), table_name='tariff')
    op.drop_table('tariff')
    op.drop_index(op.f('ix_refund_id'), table_name='refund')
    op.drop_table('refund')
