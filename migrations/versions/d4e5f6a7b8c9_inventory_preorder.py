"""inventory + pre-order

ProductVariant.allow_preorder, OrderItem.is_preorder.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-17

"""
from alembic import op
import sqlalchemy as sa


revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("product_variants", schema=None) as b:
        b.add_column(sa.Column("allow_preorder", sa.Boolean(), nullable=False,
                               server_default=sa.true()))
    with op.batch_alter_table("order_items", schema=None) as b:
        b.add_column(sa.Column("is_preorder", sa.Boolean(), nullable=False,
                               server_default=sa.false()))


def downgrade():
    with op.batch_alter_table("order_items", schema=None) as b:
        b.drop_column("is_preorder")
    with op.batch_alter_table("product_variants", schema=None) as b:
        b.drop_column("allow_preorder")
