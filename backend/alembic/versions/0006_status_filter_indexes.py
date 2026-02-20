"""status filter and bulk action indexes

Revision ID: 0006_status_filter_indexes
Revises: 0005_wallet_transactions_and_sms_inbox
Create Date: 2026-02-20 18:00:00.000000
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "0006_status_filter_indexes"
down_revision = "0005_wallet_transactions_and_sms_inbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Latest-status lookup per (company, phone) used by status filters and bulk actions.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_call_results_company_phone_id_desc "
        "ON call_results (company_id, phone_number_id, id DESC)"
    )
    # Time-bounded status aggregates (dashboard + date filters).
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_call_results_company_status_attempted "
        "ON call_results (company_id, status, attempted_at DESC)"
    )
    # Global-status filter fast path.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_numbers_global_status "
        "ON numbers (global_status)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_numbers_global_status")
    op.execute("DROP INDEX IF EXISTS ix_call_results_company_status_attempted")
    op.execute("DROP INDEX IF EXISTS ix_call_results_company_phone_id_desc")

