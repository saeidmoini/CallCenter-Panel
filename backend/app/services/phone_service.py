from datetime import datetime, timezone
import re
from typing import Iterable, Sequence

from fastapi import HTTPException
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session

from ..models.phone_number import PhoneNumber, CallStatus
from ..models.call_attempt import CallAttempt
from ..schemas.phone_number import PhoneNumberCreate, PhoneNumberStatusUpdate, PhoneNumberBulkAction, PhoneNumberBulkResult

PHONE_PATTERN = re.compile(r"^09\d{9}$")


def normalize_phone(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("0098"):
        digits = "0" + digits[4:]
    elif digits.startswith("98"):
        digits = "0" + digits[2:]
    elif digits.startswith("+98"):
        digits = "0" + digits[3:]
    if digits.startswith("9") and len(digits) == 10:
        digits = "0" + digits
    if not PHONE_PATTERN.match(digits):
        return None
    return digits


def add_numbers(db: Session, payload: PhoneNumberCreate):
    normalized = [normalize_phone(p) for p in payload.phone_numbers]
    invalid_numbers = [p for p, norm in zip(payload.phone_numbers, normalized) if norm is None]
    valid_numbers = [norm for norm in normalized if norm]
    existing_numbers = set(
        n[0]
        for n in db.execute(select(PhoneNumber.phone_number).where(PhoneNumber.phone_number.in_(valid_numbers)))
    )
    to_insert = [n for n in valid_numbers if n not in existing_numbers]

    for number in to_insert:
        db.add(PhoneNumber(phone_number=number, status=CallStatus.IN_QUEUE))
    db.commit()

    return {
        "inserted": len(to_insert),
        "duplicates": len(valid_numbers) - len(to_insert),
        "invalid": len(invalid_numbers),
        "invalid_samples": invalid_numbers[:5],
    }


def list_numbers(
    db: Session,
    status: CallStatus | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    query = db.query(PhoneNumber)
    if status:
        query = query.filter(PhoneNumber.status == status)
    if search:
        query = query.filter(PhoneNumber.phone_number.ilike(f"%{search}%"))

    sort_map = {
        "created_at": PhoneNumber.created_at,
        "last_attempt_at": PhoneNumber.last_attempt_at,
        "status": PhoneNumber.status,
    }
    column = sort_map.get(sort_by, PhoneNumber.created_at)
    if sort_order == "asc":
        query = query.order_by(column.asc().nulls_last())
    else:
        query = query.order_by(column.desc().nulls_last())

    return query.offset(skip).limit(limit).all()


def count_numbers(db: Session, status: CallStatus | None = None, search: str | None = None) -> int:
    query = db.query(func.count(PhoneNumber.id))
    if status:
        query = query.filter(PhoneNumber.status == status)
    if search:
        query = query.filter(PhoneNumber.phone_number.ilike(f"%{search}%"))
    return query.scalar() or 0


def update_number_status(db: Session, number_id: int, data: PhoneNumberStatusUpdate) -> PhoneNumber:
    number = db.get(PhoneNumber, number_id)
    if not number:
        raise HTTPException(status_code=404, detail="Number not found")
    number.status = data.status
    number.last_status_change_at = datetime.now(timezone.utc)
    if data.note:
        number.note = data.note
    db.commit()
    db.refresh(number)
    return number


def bulk_reset(db: Session, ids: Iterable[int], status: CallStatus = CallStatus.IN_QUEUE) -> int:
    numbers = db.query(PhoneNumber).filter(PhoneNumber.id.in_(list(ids))).all()
    for num in numbers:
        num.status = status
        num.assigned_at = None
        num.assigned_batch_id = None
        num.total_attempts = 0
        num.last_attempt_at = None
        num.last_status_change_at = datetime.now(timezone.utc)
    db.commit()
    return len(numbers)


def delete_number(db: Session, number_id: int) -> None:
    number = db.get(PhoneNumber, number_id)
    if not number:
        raise HTTPException(status_code=404, detail="Number not found")
    db.query(CallAttempt).filter(CallAttempt.phone_number_id == number_id).delete(synchronize_session=False)
    db.delete(number)
    db.commit()


def reset_number(db: Session, number_id: int) -> PhoneNumber:
    number = db.get(PhoneNumber, number_id)
    if not number:
        raise HTTPException(status_code=404, detail="Number not found")
    number.status = CallStatus.IN_QUEUE
    number.assigned_at = None
    number.assigned_batch_id = None
    number.total_attempts = 0
    number.last_attempt_at = None
    number.last_status_change_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(number)
    return number


def _build_query(
    db: Session,
    select_all: bool,
    ids: Sequence[int],
    filter_status: CallStatus | None,
    search: str | None,
    excluded_ids: Sequence[int],
):
    query = db.query(PhoneNumber)
    if filter_status:
        query = query.filter(PhoneNumber.status == filter_status)
    if search:
        query = query.filter(PhoneNumber.phone_number.ilike(f"%{search}%"))
    if select_all:
        if excluded_ids:
            query = query.filter(~PhoneNumber.id.in_(excluded_ids))
    else:
        query = query.filter(PhoneNumber.id.in_(ids))
    return query


def bulk_action(db: Session, payload: PhoneNumberBulkAction) -> PhoneNumberBulkResult:
    if not payload.select_all and not payload.ids:
        raise HTTPException(status_code=400, detail="No numbers selected")

    query = _build_query(
        db,
        select_all=payload.select_all,
        ids=payload.ids,
        filter_status=payload.filter_status,
        search=payload.search,
        excluded_ids=payload.excluded_ids,
    )

    result = PhoneNumberBulkResult()

    if payload.action == "delete":
        id_subquery = query.with_entities(PhoneNumber.id)
        db.query(CallAttempt).filter(CallAttempt.phone_number_id.in_(id_subquery)).delete(synchronize_session=False)
        result.deleted = query.delete(synchronize_session=False)
        db.commit()
        return result

    if payload.action == "reset":
        now = datetime.now(timezone.utc)
        result.reset = (
            query.update(
                {
                    PhoneNumber.status: CallStatus.IN_QUEUE,
                    PhoneNumber.assigned_at: None,
                    PhoneNumber.assigned_batch_id: None,
                    PhoneNumber.total_attempts: 0,
                    PhoneNumber.last_attempt_at: None,
                    PhoneNumber.last_status_change_at: now,
                },
                synchronize_session=False,
            )
            or 0
        )
        db.commit()
        return result

    if payload.action == "update_status":
        if not payload.status:
            raise HTTPException(status_code=400, detail="status is required for update_status action")
        now = datetime.now(timezone.utc)
        updates = {
            PhoneNumber.status: payload.status,
            PhoneNumber.last_status_change_at: now,
        }
        if payload.note is not None:
            updates[PhoneNumber.note] = payload.note
        result.updated = query.update(updates, synchronize_session=False) or 0
        db.commit()
        return result

    raise HTTPException(status_code=400, detail="Unsupported action")
