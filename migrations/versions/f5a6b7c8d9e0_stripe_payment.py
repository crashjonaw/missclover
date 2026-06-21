"""stripe payment

Replace HitPay order columns with Stripe PaymentIntent tracking.

Revision ID: f5a6b7c8d9e0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-22

"""
from alembic import op
import sqlalchemy as sa


revision = 'f5a6b7c8d9e0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("orders", schema=None) as b:
        b.add_column(sa.Column("stripe_payment_intent_id", sa.String(length=80), nullable=True))
        b.add_column(sa.Column("stripe_status", sa.String(length=40), nullable=True))
        b.create_index(b.f("ix_orders_stripe_payment_intent_id"),
                       ["stripe_payment_intent_id"], unique=False)
        b.drop_column("hitpay_payment_request_id")
        b.drop_column("hitpay_reference")
        b.drop_column("hitpay_status")


def downgrade():
    with op.batch_alter_table("orders", schema=None) as b:
        b.add_column(sa.Column("hitpay_status", sa.String(length=40), nullable=True))
        b.add_column(sa.Column("hitpay_reference", sa.String(length=80), nullable=True))
        b.add_column(sa.Column("hitpay_payment_request_id", sa.String(length=80), nullable=True))
        b.drop_index(b.f("ix_orders_stripe_payment_intent_id"))
        b.drop_column("stripe_status")
        b.drop_column("stripe_payment_intent_id")
