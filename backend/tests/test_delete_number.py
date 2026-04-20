from datetime import datetime, timezone

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models import AdminUser, CallResult, Company, DialerBatchItem, PhoneNumber, UserRole
from app.models.phone_number import CallStatus, GlobalStatus
from app.services.phone_service import delete_number


def _sqlite_session():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def test_delete_number_removes_related_dialer_batch_items():
    db = _sqlite_session()

    company = Company(name="salehi", display_name="Salehi", settings={})
    db.add(company)
    db.flush()

    admin = AdminUser(
        username="admin",
        password_hash="x",
        is_superuser=True,
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)

    number = PhoneNumber(phone_number="09105881921", global_status=GlobalStatus.ACTIVE)
    db.add(number)
    db.flush()

    call_result = CallResult(
        phone_number_id=number.id,
        company_id=company.id,
        status=CallStatus.MISSED,
        attempted_at=datetime.now(timezone.utc),
    )
    db.add(call_result)
    db.flush()

    batch_item = DialerBatchItem(
        batch_id="batch-1",
        company_id=company.id,
        phone_number_id=number.id,
        assigned_at=datetime.now(timezone.utc),
        report_call_result_id=call_result.id,
    )
    db.add(batch_item)
    db.commit()

    delete_number(db, number.id, current_user=admin, company_name="salehi")

    assert db.get(PhoneNumber, number.id) is None
    assert db.query(CallResult).filter(CallResult.phone_number_id == number.id).count() == 0
    assert db.query(DialerBatchItem).filter(DialerBatchItem.phone_number_id == number.id).count() == 0
