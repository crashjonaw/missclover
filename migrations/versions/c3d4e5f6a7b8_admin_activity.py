"""admin + activity analytics

users.username + users.is_admin; activity_events table (commerce-funnel log).

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-17

"""
from alembic import op
import sqlalchemy as sa


revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as b:
        b.add_column(sa.Column("username", sa.String(length=80), nullable=True))
        b.add_column(sa.Column("is_admin", sa.Boolean(), nullable=False,
                               server_default=sa.false()))
        b.create_index(b.f("ix_users_username"), ["username"], unique=True)
        b.create_index(b.f("ix_users_is_admin"), ["is_admin"], unique=False)

    op.create_table(
        "activity_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("anon_id", sa.String(length=64), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("value_cents", sa.Integer(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("ip", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("activity_events", schema=None) as b:
        b.create_index(b.f("ix_activity_events_user_id"), ["user_id"])
        b.create_index(b.f("ix_activity_events_anon_id"), ["anon_id"])
        b.create_index(b.f("ix_activity_events_event_type"), ["event_type"])
        b.create_index(b.f("ix_activity_events_product_id"), ["product_id"])
        b.create_index(b.f("ix_activity_events_order_id"), ["order_id"])
        b.create_index(b.f("ix_activity_events_created_at"), ["created_at"])


def downgrade():
    op.drop_table("activity_events")
    with op.batch_alter_table("users", schema=None) as b:
        b.drop_index(b.f("ix_users_is_admin"))
        b.drop_index(b.f("ix_users_username"))
        b.drop_column("is_admin")
        b.drop_column("username")
