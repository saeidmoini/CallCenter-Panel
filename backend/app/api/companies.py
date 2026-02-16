from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..api.deps import get_superuser
from ..schemas.company import CompanyCreate, CompanyUpdate, CompanyOut
from ..models.company import Company

router = APIRouter(dependencies=[Depends(get_superuser)])


@router.get("/", response_model=list[CompanyOut])
def list_companies(db: Session = Depends(get_db)):
    """List all companies (superuser only)"""
    return db.query(Company).all()


@router.get("/{company_name}", response_model=CompanyOut)
def get_company(company_name: str, db: Session = Depends(get_db)):
    """Get company by name"""
    company = db.query(Company).filter(Company.name == company_name).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/", response_model=CompanyOut)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    """Create a new company (superuser only)"""
    # Check if company name already exists
    existing = db.query(Company).filter(Company.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Company name already exists")

    company = Company(
        name=payload.name,
        display_name=payload.display_name,
        is_active=payload.is_active,
        settings=payload.settings,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.put("/{company_id}", response_model=CompanyOut)
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)):
    """Update company (superuser only)"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if payload.display_name is not None:
        company.display_name = payload.display_name
    if payload.is_active is not None:
        company.is_active = payload.is_active
    if payload.settings is not None:
        company.settings = payload.settings

    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}")
def deactivate_company(company_id: int, db: Session = Depends(get_db)):
    """Deactivate company (soft delete - superuser only)"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company.is_active = False
    db.commit()
    return {"deleted": True, "id": company_id}
