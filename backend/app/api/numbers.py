import csv
import io
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session

from ..api.deps import get_active_admin
from ..core.db import get_db
from ..models.phone_number import CallStatus
from ..schemas.phone_number import (
    PhoneNumberCreate,
    PhoneNumberOut,
    PhoneNumberStatusUpdate,
    PhoneNumberImportResponse,
    PhoneNumberStatsResponse,
    PhoneNumberBulkAction,
    PhoneNumberBulkResult,
)
from ..services import phone_service

router = APIRouter(dependencies=[Depends(get_active_admin)])


@router.get("/", response_model=list[PhoneNumberOut])
def list_numbers(
    status: CallStatus | None = Query(default=None),
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
    sort_by: str = Query(default="created_at", pattern="^(created_at|last_attempt_at|status)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    numbers = phone_service.list_numbers(
        db, status=status, search=search, skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order
    )
    return numbers


@router.get("/stats", response_model=PhoneNumberStatsResponse)
def numbers_stats(
    status: CallStatus | None = Query(default=None),
    search: str | None = None,
    db: Session = Depends(get_db),
):
    total = phone_service.count_numbers(db, status=status, search=search)
    return PhoneNumberStatsResponse(total=total)


@router.post("/", response_model=PhoneNumberImportResponse)
def add_numbers(payload: PhoneNumberCreate, db: Session = Depends(get_db)):
    result = phone_service.add_numbers(db, payload)
    return PhoneNumberImportResponse(**result)


@router.post("/upload", response_model=PhoneNumberImportResponse)
def upload_numbers(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = file.file.read()
    file.file.close()
    if file.filename.endswith(".csv"):
        decoded = content.decode("utf-8")
        reader = csv.reader(io.StringIO(decoded))
        numbers = [row[0] for row in reader if row]
    else:
        try:
            import openpyxl
        except ImportError:  # pragma: no cover
            raise RuntimeError("openpyxl not installed")
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        sheet = wb.active
        numbers = []
        for row in sheet.iter_rows(min_row=1, max_col=1, values_only=True):
            val = row[0]
            if val:
                numbers.append(str(val))
    result = phone_service.add_numbers(db, PhoneNumberCreate(phone_numbers=numbers))
    return PhoneNumberImportResponse(**result)


@router.put("/{number_id}/status", response_model=PhoneNumberOut)
def update_status(number_id: int, payload: PhoneNumberStatusUpdate, db: Session = Depends(get_db)):
    number = phone_service.update_number_status(db, number_id, payload)
    return number


@router.delete("/{number_id}")
def delete_number(number_id: int, db: Session = Depends(get_db)):
    phone_service.delete_number(db, number_id)
    return {"deleted": True, "id": number_id}


@router.post("/{number_id}/reset", response_model=PhoneNumberOut)
def reset_number(number_id: int, db: Session = Depends(get_db)):
    number = phone_service.reset_number(db, number_id)
    return number


@router.post("/bulk", response_model=PhoneNumberBulkResult)
def bulk_numbers_action(payload: PhoneNumberBulkAction, db: Session = Depends(get_db)):
    return phone_service.bulk_action(db, payload)
