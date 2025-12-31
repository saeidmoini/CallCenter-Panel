"""add roles, agents, and new call statuses

Revision ID: 0002_roles_agents_and_statuses
Revises: 0001_initial
Create Date: 2024-01-01 01:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_roles_agents_and_statuses"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend callstatus enum with new values
    op.execute("ALTER TYPE callstatus ADD VALUE IF NOT EXISTS 'BUSY'")
    op.execute("ALTER TYPE callstatus ADD VALUE IF NOT EXISTS 'POWER_OFF'")
    op.execute("ALTER TYPE callstatus ADD VALUE IF NOT EXISTS 'BANNED'")
    op.execute("ALTER TYPE callstatus ADD VALUE IF NOT EXISTS 'UNKNOWN'")

    userrole = sa.Enum("ADMIN", "AGENT", name="userrole")
    userrole.create(op.get_bind(), checkfirst=True)

    op.add_column("admin_users", sa.Column("role", userrole, nullable=True, server_default="ADMIN"))
    op.add_column("admin_users", sa.Column("first_name", sa.String(length=100), nullable=True))
    op.add_column("admin_users", sa.Column("last_name", sa.String(length=100), nullable=True))
    op.add_column("admin_users", sa.Column("phone_number", sa.String(length=32), nullable=True))
    op.create_unique_constraint("uq_admin_users_phone_number", "admin_users", ["phone_number"])
    op.execute("UPDATE admin_users SET role='ADMIN' WHERE role IS NULL")
    op.alter_column("admin_users", "role", nullable=False, server_default=None)

    op.add_column("phone_numbers", sa.Column("last_user_message", sa.String(length=1000), nullable=True))
    op.add_column("phone_numbers", sa.Column("assigned_agent_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_phone_numbers_assigned_agent",
        "phone_numbers",
        "admin_users",
        ["assigned_agent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_phone_numbers_assigned_agent_id", "phone_numbers", ["assigned_agent_id"], unique=False)

    op.add_column("call_attempts", sa.Column("user_message", sa.String(length=1000), nullable=True))
    op.add_column("call_attempts", sa.Column("agent_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_call_attempts_agent",
        "call_attempts",
        "admin_users",
        ["agent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_call_attempts_agent_id", "call_attempts", ["agent_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_call_attempts_agent_id", table_name="call_attempts")
    op.drop_constraint("fk_call_attempts_agent", "call_attempts", type_="foreignkey")
    op.drop_column("call_attempts", "agent_id")
    op.drop_column("call_attempts", "user_message")

    op.drop_index("ix_phone_numbers_assigned_agent_id", table_name="phone_numbers")
    op.drop_constraint("fk_phone_numbers_assigned_agent", "phone_numbers", type_="foreignkey")
    op.drop_column("phone_numbers", "assigned_agent_id")
    op.drop_column("phone_numbers", "last_user_message")

    op.drop_constraint("uq_admin_users_phone_number", "admin_users", type_="unique")
    op.drop_column("admin_users", "phone_number")
    op.drop_column("admin_users", "last_name")
    op.drop_column("admin_users", "first_name")
    op.drop_column("admin_users", "role")
    userrole = sa.Enum("ADMIN", "AGENT", name="userrole")
    userrole.drop(op.get_bind(), checkfirst=True)
    # callstatus enum values cannot be removed in PostgreSQL; downgrade leaves them in place.
