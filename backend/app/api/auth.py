from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..schemas.auth import LoginRequest, Token
from ..core.security import get_current_active_user
from ..schemas.user import AdminUserOut, AdminSelfUpdate
from ..services import auth_service
from ..models.company import Company

router = APIRouter()


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token = auth_service.authenticate_user(db, payload)
    return Token(access_token=token)


@router.get("/me", response_model=AdminUserOut)
def get_me(
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get current user profile with company name"""
    # Add company_name if user has a company
    if current_user.company_id:
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        if company:
            current_user.company_name = company.name
    return current_user


@router.put("/me", response_model=AdminUserOut)
def update_me(
    payload: AdminSelfUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Update current user profile"""
    updated_user = auth_service.update_self(db, current_user.id, payload)
    # Add company_name if user has a company
    if updated_user.company_id:
        company = db.query(Company).filter(Company.id == updated_user.company_id).first()
        if company:
            updated_user.company_name = company.name
    return updated_user
