from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from ..api.deps import get_dialer_auth
from ..core.db import get_db
from ..schemas.dialer import NextBatchResponse, DialerReport
from ..schemas.scenario import RegisterScenariosRequest
from ..services import dialer_service
from ..models.company import Company
from ..models.scenario import Scenario

router = APIRouter(dependencies=[Depends(get_dialer_auth)])


@router.get("/next-batch", response_model=NextBatchResponse)
def next_batch(
    company: str = Query(..., description="Company slug"),
    size: int | None = Query(default=None, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Fetch next batch of numbers for a company"""
    company_obj = db.query(Company).filter(Company.name == company, Company.is_active == True).first()
    if not company_obj:
        raise HTTPException(status_code=404, detail="Company not found")

    payload = dialer_service.fetch_next_batch(db, company=company_obj, size=size)
    return payload


@router.post("/report-result")
def report_result(report: DialerReport, db: Session = Depends(get_db)):
    """Report call result for a company"""
    company_obj = db.query(Company).filter(Company.name == report.company, Company.is_active == True).first()
    if not company_obj:
        raise HTTPException(status_code=404, detail="Company not found")

    number = dialer_service.report_result(db, report, company=company_obj)
    return {"id": number.id, "global_status": number.global_status}


@router.post("/register-scenarios")
def register_scenarios(
    payload: RegisterScenariosRequest,
    db: Session = Depends(get_db),
):
    """Dialer app registers available scenarios on startup"""
    company_obj = db.query(Company).filter(Company.name == payload.company, Company.is_active == True).first()
    if not company_obj:
        raise HTTPException(status_code=404, detail="Company not found")

    for s in payload.scenarios:
        existing = db.query(Scenario).filter(
            Scenario.company_id == company_obj.id,
            Scenario.name == s.name
        ).first()
        if existing:
            existing.display_name = s.display_name
        else:
            db.add(Scenario(
                company_id=company_obj.id,
                name=s.name,
                display_name=s.display_name,
                is_active=True
            ))
    db.commit()
    return {"registered": len(payload.scenarios)}
