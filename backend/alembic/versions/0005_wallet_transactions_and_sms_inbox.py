"""wallet transactions and bank sms inbox

Revision ID: 0005_wallet_transactions_and_sms_inbox
Revises: 0004_multi_company
Create Date: 2026-02-18 20:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0005_wallet_transactions_and_sms_inbox"
down_revision = "0004_multi_company"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bank_incoming_sms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sender", sa.String(length=32), nullable=False),
        sa.Column("receiver", sa.String(length=32), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_bank_sender", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("parsed_amount_rial", sa.Integer(), nullable=True),
        sa.Column("parsed_amount_toman", sa.Integer(), nullable=True),
        sa.Column("parsed_transaction_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("parsed_is_credit", sa.Boolean(), nullable=True),
        sa.Column("parse_error", sa.String(length=255), nullable=True),
        sa.Column("consumed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bank_incoming_sms_sender"), "bank_incoming_sms", ["sender"], unique=False)
    op.create_index(op.f("ix_bank_incoming_sms_parsed_amount_toman"), "bank_incoming_sms", ["parsed_amount_toman"], unique=False)
    op.create_index(op.f("ix_bank_incoming_sms_parsed_transaction_at"), "bank_incoming_sms", ["parsed_transaction_at"], unique=False)
    op.create_index(op.f("ix_bank_incoming_sms_parsed_is_credit"), "bank_incoming_sms", ["parsed_is_credit"], unique=False)
    op.create_index(op.f("ix_bank_incoming_sms_consumed"), "bank_incoming_sms", ["consumed"], unique=False)
    op.create_index(op.f("ix_bank_incoming_sms_received_at"), "bank_incoming_sms", ["received_at"], unique=False)

    op.create_table(
        "wallet_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("amount_toman", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("transaction_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("bank_sms_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["bank_sms_id"], ["bank_incoming_sms.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["admin_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bank_sms_id"),
    )
    op.create_index(op.f("ix_wallet_transactions_company_id"), "wallet_transactions", ["company_id"], unique=False)
    op.create_index(op.f("ix_wallet_transactions_transaction_at"), "wallet_transactions", ["transaction_at"], unique=False)
    op.create_index(op.f("ix_wallet_transactions_created_by_user_id"), "wallet_transactions", ["created_by_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_wallet_transactions_created_by_user_id"), table_name="wallet_transactions")
    op.drop_index(op.f("ix_wallet_transactions_transaction_at"), table_name="wallet_transactions")
    op.drop_index(op.f("ix_wallet_transactions_company_id"), table_name="wallet_transactions")
    op.drop_table("wallet_transactions")

    op.drop_index(op.f("ix_bank_incoming_sms_received_at"), table_name="bank_incoming_sms")
    op.drop_index(op.f("ix_bank_incoming_sms_consumed"), table_name="bank_incoming_sms")
    op.drop_index(op.f("ix_bank_incoming_sms_parsed_is_credit"), table_name="bank_incoming_sms")
    op.drop_index(op.f("ix_bank_incoming_sms_parsed_transaction_at"), table_name="bank_incoming_sms")
    op.drop_index(op.f("ix_bank_incoming_sms_parsed_amount_toman"), table_name="bank_incoming_sms")
    op.drop_index(op.f("ix_bank_incoming_sms_sender"), table_name="bank_incoming_sms")
    op.drop_table("bank_incoming_sms")
