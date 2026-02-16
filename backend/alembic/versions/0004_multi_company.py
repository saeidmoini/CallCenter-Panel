"""multi-company support with scenarios and outbound lines

Revision ID: 0004_multi_company
Revises: 0003_superuser_first_admin
Create Date: 2026-02-14 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0004_multi_company"
down_revision = "0003_superuser_first_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ===== 1. Add new enum types =====

    # Add INBOUND_CALL to existing callstatus enum
    op.execute("ALTER TYPE callstatus ADD VALUE IF NOT EXISTS 'INBOUND_CALL'")

    # Create new enums
    op.execute("CREATE TYPE globalstatus AS ENUM ('ACTIVE', 'COMPLAINED', 'POWER_OFF')")
    op.execute("CREATE TYPE agenttype AS ENUM ('INBOUND', 'OUTBOUND', 'BOTH')")

    # ===== 2. Create companies table =====
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('settings', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_companies_name'), 'companies', ['name'], unique=True)

    # ===== 3. Create scenarios table =====
    op.create_table(
        'scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'name', name='uq_scenarios_company_name')
    )
    op.create_index(op.f('ix_scenarios_company_id'), 'scenarios', ['company_id'], unique=False)

    # ===== 4. Create outbound_lines table =====
    op.create_table(
        'outbound_lines',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('phone_number', sa.String(length=32), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'phone_number', name='uq_outbound_lines_company_phone')
    )
    op.create_index(op.f('ix_outbound_lines_company_id'), 'outbound_lines', ['company_id'], unique=False)

    # ===== 5. Alter admin_users table =====
    op.add_column('admin_users', sa.Column('company_id', sa.Integer(), nullable=True))
    op.add_column('admin_users', sa.Column('agent_type', postgresql.ENUM('INBOUND', 'OUTBOUND', 'BOTH', name='agenttype'), nullable=False, server_default='BOTH'))
    op.create_foreign_key('fk_admin_users_company_id', 'admin_users', 'companies', ['company_id'], ['id'])
    op.create_index(op.f('ix_admin_users_company_id'), 'admin_users', ['company_id'], unique=False)
    op.execute("ALTER TABLE admin_users ALTER COLUMN agent_type DROP DEFAULT")

    # ===== 6. Rename and alter phone_numbers → numbers =====
    op.rename_table('phone_numbers', 'numbers')

    # Add new columns to numbers table
    op.add_column('numbers', sa.Column('global_status', postgresql.ENUM('ACTIVE', 'COMPLAINED', 'POWER_OFF', name='globalstatus'), nullable=False, server_default='ACTIVE'))
    op.add_column('numbers', sa.Column('last_called_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('numbers', sa.Column('last_called_company_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_numbers_last_called_company_id', 'numbers', 'companies', ['last_called_company_id'], ['id'])
    op.execute("ALTER TABLE numbers ALTER COLUMN global_status DROP DEFAULT")

    # Rename indexes
    op.execute("ALTER INDEX IF EXISTS ix_phone_numbers_phone_number RENAME TO ix_numbers_phone_number")

    # Critical performance index for queue queries
    op.create_index('ix_numbers_global_status_last_called', 'numbers', ['global_status', 'last_called_at'], unique=False)

    # ===== 7. Rename and alter call_attempts → call_results =====
    op.rename_table('call_attempts', 'call_results')

    # Add new columns to call_results table
    op.add_column('call_results', sa.Column('company_id', sa.Integer(), nullable=True))
    op.add_column('call_results', sa.Column('scenario_id', sa.Integer(), nullable=True))
    op.add_column('call_results', sa.Column('outbound_line_id', sa.Integer(), nullable=True))

    op.create_foreign_key('fk_call_results_company_id', 'call_results', 'companies', ['company_id'], ['id'])
    op.create_foreign_key('fk_call_results_scenario_id', 'call_results', 'scenarios', ['scenario_id'], ['id'])
    op.create_foreign_key('fk_call_results_outbound_line_id', 'call_results', 'outbound_lines', ['outbound_line_id'], ['id'])

    # Rename indexes and constraints
    op.execute("ALTER INDEX IF EXISTS ix_call_attempts_attempted_at RENAME TO ix_call_results_attempted_at")
    op.execute("ALTER INDEX IF EXISTS ix_call_attempts_phone_number_id RENAME TO ix_call_results_phone_number_id")

    # Critical performance indexes for 1.9M+ records
    op.create_index('ix_call_results_company_attempted', 'call_results', ['company_id', 'attempted_at'], unique=False)
    op.create_index('ix_call_results_company_status', 'call_results', ['company_id', 'status'], unique=False)
    op.create_index('ix_call_results_phone_company', 'call_results', ['phone_number_id', 'company_id'], unique=False)

    # ===== 8. Alter schedule_configs and schedule_windows for per-company =====
    op.add_column('schedule_configs', sa.Column('company_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_schedule_configs_company_id', 'schedule_configs', 'companies', ['company_id'], ['id'])
    op.create_index('uq_schedule_configs_company', 'schedule_configs', ['company_id'], unique=True)

    op.add_column('schedule_windows', sa.Column('company_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_schedule_windows_company_id', 'schedule_windows', 'companies', ['company_id'], ['id'])
    op.create_index(op.f('ix_schedule_windows_company_id'), 'schedule_windows', ['company_id'], unique=False)

    # ===== 9. Seed initial data =====

    # Insert companies
    op.execute("""
        INSERT INTO companies (name, display_name) VALUES
        ('salehi', 'صالحی'),
        ('agrad', 'اگرد');
    """)

    # Create default scenario for salehi
    op.execute("""
        INSERT INTO scenarios (company_id, name, display_name, is_active)
        SELECT id, 'default', 'سناریوی پیش‌فرض', TRUE
        FROM companies WHERE name='salehi';
    """)

    # Create outbound lines for salehi (4 phone numbers)
    op.execute("""
        INSERT INTO outbound_lines (company_id, phone_number, display_name, is_active)
        SELECT
            c.id,
            lines.phone_number,
            lines.display_name,
            TRUE
        FROM companies c
        CROSS JOIN (
            VALUES
                ('02191302954', 'خط 1 - تهران'),
                ('09422092601', 'خط 2 - موبایل'),
                ('09422092653', 'خط 3 - موبایل'),
                ('09422092817', 'خط 4 - موبایل')
        ) AS lines(phone_number, display_name)
        WHERE c.name = 'salehi';
    """)

    # Assign existing users to 'salehi' (except superuser stays null)
    op.execute("""
        UPDATE admin_users
        SET company_id = (SELECT id FROM companies WHERE name='salehi')
        WHERE is_superuser = FALSE;
    """)

    # Assign existing call_results to 'salehi' and default scenario
    # Also distribute calls equally among the 4 outbound lines
    op.execute("""
        WITH salehi_data AS (
            SELECT
                c.id as company_id,
                s.id as scenario_id
            FROM companies c
            JOIN scenarios s ON s.company_id = c.id
            WHERE c.name = 'salehi' AND s.name = 'default'
        ),
        outbound_lines_array AS (
            SELECT array_agg(id ORDER BY id) as line_ids
            FROM outbound_lines
            WHERE company_id = (SELECT id FROM companies WHERE name='salehi')
        ),
        ranked_calls AS (
            SELECT
                id,
                ROW_NUMBER() OVER (ORDER BY attempted_at) as rn
            FROM call_results
        )
        UPDATE call_results cr
        SET
            company_id = sd.company_id,
            scenario_id = sd.scenario_id,
            outbound_line_id = (
                SELECT line_ids[(rc.rn - 1) % array_length(line_ids, 1) + 1]
                FROM outbound_lines_array, ranked_calls rc
                WHERE rc.id = cr.id
            )
        FROM salehi_data sd;
    """)

    # Assign existing schedules to 'salehi'
    op.execute("""
        UPDATE schedule_configs
        SET company_id = (SELECT id FROM companies WHERE name='salehi');
    """)

    op.execute("""
        UPDATE schedule_windows
        SET company_id = (SELECT id FROM companies WHERE name='salehi');
    """)


def downgrade() -> None:
    # Reverse all changes in opposite order

    # Remove company references from schedule tables
    op.execute("UPDATE schedule_windows SET company_id = NULL")
    op.execute("UPDATE schedule_configs SET company_id = NULL")
    op.drop_index(op.f('ix_schedule_windows_company_id'), table_name='schedule_windows')
    op.drop_constraint('fk_schedule_windows_company_id', 'schedule_windows', type_='foreignkey')
    op.drop_column('schedule_windows', 'company_id')

    op.drop_index('uq_schedule_configs_company', table_name='schedule_configs')
    op.drop_constraint('fk_schedule_configs_company_id', 'schedule_configs', type_='foreignkey')
    op.drop_column('schedule_configs', 'company_id')

    # Remove indexes and columns from call_results
    op.drop_index('ix_call_results_phone_company', table_name='call_results')
    op.drop_index('ix_call_results_company_status', table_name='call_results')
    op.drop_index('ix_call_results_company_attempted', table_name='call_results')

    op.execute("ALTER INDEX IF EXISTS ix_call_results_phone_number_id RENAME TO ix_call_attempts_phone_number_id")
    op.execute("ALTER INDEX IF EXISTS ix_call_results_attempted_at RENAME TO ix_call_attempts_attempted_at")

    op.drop_constraint('fk_call_results_outbound_line_id', 'call_results', type_='foreignkey')
    op.drop_constraint('fk_call_results_scenario_id', 'call_results', type_='foreignkey')
    op.drop_constraint('fk_call_results_company_id', 'call_results', type_='foreignkey')
    op.drop_column('call_results', 'outbound_line_id')
    op.drop_column('call_results', 'scenario_id')
    op.drop_column('call_results', 'company_id')

    op.rename_table('call_results', 'call_attempts')

    # Remove columns from numbers table
    op.drop_index('ix_numbers_global_status_last_called', table_name='numbers')
    op.execute("ALTER INDEX IF EXISTS ix_numbers_phone_number RENAME TO ix_phone_numbers_phone_number")

    op.drop_constraint('fk_numbers_last_called_company_id', 'numbers', type_='foreignkey')
    op.drop_column('numbers', 'last_called_company_id')
    op.drop_column('numbers', 'last_called_at')
    op.drop_column('numbers', 'global_status')

    op.rename_table('numbers', 'phone_numbers')

    # Remove columns from admin_users
    op.drop_index(op.f('ix_admin_users_company_id'), table_name='admin_users')
    op.drop_constraint('fk_admin_users_company_id', 'admin_users', type_='foreignkey')
    op.drop_column('admin_users', 'agent_type')
    op.drop_column('admin_users', 'company_id')

    # Drop new tables
    op.drop_table('outbound_lines')
    op.drop_table('scenarios')
    op.drop_table('companies')

    # Drop new enums
    op.execute("DROP TYPE agenttype")
    op.execute("DROP TYPE globalstatus")
