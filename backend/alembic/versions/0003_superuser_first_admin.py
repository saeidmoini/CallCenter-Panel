"""add is_superuser flag and set first admin

Revision ID: 0003_superuser_first_admin
Revises: 0002_roles_agents_and_statuses
Create Date: 2024-01-01 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_superuser_first_admin"
down_revision = "0002_roles_agents_and_statuses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("admin_users", sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.execute(
        """
        UPDATE admin_users
        SET is_superuser = TRUE
        WHERE id = (SELECT id FROM admin_users ORDER BY id ASC LIMIT 1)
        """
    )
    op.execute("ALTER TABLE admin_users ALTER COLUMN is_superuser DROP DEFAULT")


def downgrade() -> None:
    op.drop_column("admin_users", "is_superuser")
