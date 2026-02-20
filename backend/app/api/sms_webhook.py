from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..services import wallet_service

router = APIRouter()


@router.get("/getsms.Php")
def receive_sms_webhook(
    to: str | None = Query(default=None),
    body: str = Query(...),
    from_number: str = Query(..., alias="from"),
    db: Session = Depends(get_db),
):
    sms = wallet_service.ingest_incoming_sms(
        db=db,
        sender=from_number,
        receiver=to,
        body=body,
    )
    return {"ok": True, "stored": bool(sms), "id": sms.id if sms else None}
