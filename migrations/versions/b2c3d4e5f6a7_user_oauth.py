"""user oauth: nullable password_hash + oauth_provider

Google-OAuth users have no local password. Make users.password_hash nullable
and add users.oauth_provider.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-17

"""
from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as b:
        b.add_column(sa.Column("oauth_provider", sa.String(length=20), nullable=True))
        b.alter_column("password_hash",
                       existing_type=sa.String(length=255),
                       nullable=True)


def downgrade():
    # Give any password-less (OAuth) users a placeholder so the NOT NULL
    # constraint can be restored without failing.
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE users SET password_hash='!oauth-no-password' WHERE password_hash IS NULL"))
    with op.batch_alter_table("users", schema=None) as b:
        b.alter_column("password_hash",
                       existing_type=sa.String(length=255),
                       nullable=False)
        b.drop_column("oauth_provider")
