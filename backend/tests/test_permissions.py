import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.core.db import Base
from app.models import PhoneNumber, CallStatus, AdminUser, UserRole
from app.schemas.phone_number import PhoneNumberStatusUpdate, PhoneNumberBulkAction
from app.services import phone_service


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_admin_cannot_change_immutable_status(db_session):
    admin = AdminUser(username="admin", password_hash="x", role=UserRole.ADMIN, is_active=True)
    number = PhoneNumber(phone_number="09123456789", status=CallStatus.CONNECTED)
    db_session.add_all([admin, number])
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        phone_service.update_number_status(
            db_session,
            number.id,
            PhoneNumberStatusUpdate(status=CallStatus.MISSED),
            current_user=admin,
        )
    assert exc.value.status_code == 400


def test_agent_cannot_touch_unassigned_number(db_session):
    agent = AdminUser(username="agent", password_hash="x", role=UserRole.AGENT, is_active=True)
    number = PhoneNumber(phone_number="09123456780", status=CallStatus.MISSED)
    db_session.add_all([agent, number])
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        phone_service.reset_number(db_session, number.id, current_user=agent)
    assert exc.value.status_code == 403


def test_agent_can_modify_assigned_number_with_mutable_status(db_session):
    agent = AdminUser(username="agent2", password_hash="x", role=UserRole.AGENT, is_active=True)
    db_session.add(agent)
    db_session.flush()
    number = PhoneNumber(
        phone_number="09123456781",
        status=CallStatus.MISSED,
        assigned_agent_id=agent.id,
    )
    db_session.add(number)
    db_session.commit()

    updated = phone_service.update_number_status(
        db_session,
        number.id,
        PhoneNumberStatusUpdate(status=CallStatus.BANNED),
        current_user=agent,
    )
    assert updated.status == CallStatus.BANNED


def test_bulk_action_blocks_immutable_statuses(db_session):
    admin = AdminUser(username="admin2", password_hash="x", role=UserRole.ADMIN, is_active=True)
    db_session.add(admin)
    db_session.flush()
    n1 = PhoneNumber(phone_number="09123456782", status=CallStatus.CONNECTED)
    n2 = PhoneNumber(phone_number="09123456783", status=CallStatus.MISSED)
    db_session.add_all([n1, n2])
    db_session.commit()

    payload = PhoneNumberBulkAction(action="delete", ids=[n1.id, n2.id], select_all=False)
    with pytest.raises(HTTPException) as exc:
        phone_service.bulk_action(db_session, payload, current_user=admin)
    assert exc.value.status_code == 400
