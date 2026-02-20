"""agent filter indexes for large datasets

Revision ID: 0007_agent_filter_indexes
Revises: 0006_status_filter_indexes
Create Date: 2026-02-20 19:30:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "0007_agent_filter_indexes"
down_revision = "0006_status_filter_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agent-scoped latest-call and timeline lookups.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_call_results_company_agent_id_desc "
        "ON call_results (company_id, agent_id, id DESC) "
        "WHERE agent_id IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_call_results_company_agent_attempted "
        "ON call_results (company_id, agent_id, attempted_at DESC) "
        "WHERE agent_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_call_results_company_agent_attempted")
    op.execute("DROP INDEX IF EXISTS ix_call_results_company_agent_id_desc")

