"""init

Revision ID: fa5675f8b70e
Revises:
Create Date: 2025-02-09 11:49:51.768075+00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "fa5675f8b70e"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refund",
        sa.Column(
            "payment_id",
            type_=sa.VARCHAR(),
            nullable=False,
        ),
        sa.Column("refund_id", sa.UUID(), nullable=False),
        sa.Column(
            "amount",
            existing_type=sa.INTEGER(),
            type_=sa.Numeric(precision=6, scale=2),
            nullable=False,
        ),
        sa.Column("status", sa.VARCHAR(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "modified",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_refund_id"),
        "refund",
        ["id"],
        unique=True,
    )

    op.create_table(
        "tariff",
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "price",
            sa.Numeric(precision=6, scale=2),
            nullable=False,
        ),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("modified", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tariff_id"),
        "tariff",
        ["id"],
        unique=True,
    )

    # Insert initial tariffs
    op.bulk_insert(
        sa.table(
            "tariff",
            sa.Column("id", sa.UUID()),
            sa.Column("name", sa.String()),
            sa.Column("description", sa.Text()),
            sa.Column("price", sa.Numeric(precision=6, scale=2)),
            sa.Column("currency", sa.String(length=3)),
            sa.Column("duration", sa.Integer()),
            sa.Column("is_active", sa.Boolean()),
        ),
        [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "name": "Basic Monthly",
                "description": "Basic subscription plan with monthly billing",
                "price": 9.99,
                "currency": "USD",
                "duration": 30,
                "is_active": True,
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "name": "Premium Monthly",
                "description": "Premium subscription with advanced features, billed monthly",
                "price": 19.99,
                "currency": "USD",
                "duration": 30,
                "is_active": True,
            },
            {
                "id": "33333333-3333-3333-3333-333333333333",
                "name": "Basic Annual",
                "description": "Basic subscription plan with annual billing, 2 months free",
                "price": 99.99,
                "currency": "USD",
                "duration": 365,
                "is_active": True,
            },
            {
                "id": "44444444-4444-4444-4444-444444444444",
                "name": "Premium Annual",
                "description": "Premium subscription with advanced features, billed annually, 2 months free",
                "price": 199.99,
                "currency": "USD",
                "duration": 365,
                "is_active": True,
            },
        ],
    )

    op.create_table(
        "payment",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("tariff_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("payment_id", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("subscription_id", sa.UUID(), nullable=False),
        sa.Column("method_id", sa.UUID(), nullable=True),
        sa.Column(
            "created",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("modified", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["tariff_id"],
            ["tariff.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_id"), table_name="payment")
    op.drop_table("payment")
    op.drop_index(op.f("ix_tariff_id"), table_name="tariff")
    op.drop_table("tariff")
    op.drop_index(op.f("ix_refund_id"), table_name="refund")
    op.drop_table("refund")
