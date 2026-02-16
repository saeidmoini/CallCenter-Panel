from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..api.deps import get_active_admin, get_company, get_company_user
from ..core.db import get_db
from ..services import schedule_service
from ..schemas.schedule import ScheduleConfigOut, ScheduleConfigUpdate, ScheduleInterval
from ..models.company import Company
from ..models.user import AdminUser

router = APIRouter()


@router.get("/{company_name}/schedule", response_model=ScheduleConfigOut, dependencies=[Depends(get_active_admin)])
def get_schedule(
    company: Company = Depends(get_company),
    user: AdminUser = Depends(get_company_user),
    db: Session = Depends(get_db),
):
    """Get company schedule configuration"""
    config = schedule_service.get_config(db, company_id=company.id)
    intervals = schedule_service.list_intervals(db, company_id=company.id)
    return ScheduleConfigOut(
        skip_holidays=config.skip_holidays,
        enabled=config.enabled,
        disabled_by_dialer=config.disabled_by_dialer or False,
        wallet_balance=config.wallet_balance or 0,
        cost_per_connected=config.cost_per_connected or 0,
        version=config.version,
        updated_at=config.updated_at,
        intervals=[
            ScheduleInterval(day_of_week=i.day_of_week, start_time=i.start_time, end_time=i.end_time)
            for i in intervals
        ],
    )


@router.put("/{company_name}/schedule", response_model=ScheduleConfigOut, dependencies=[Depends(get_active_admin)])
def update_schedule(
    payload: ScheduleConfigUpdate,
    company: Company = Depends(get_company),
    user: AdminUser = Depends(get_company_user),
    db: Session = Depends(get_db),
):
    """Update company schedule configuration"""
    config = schedule_service.update_schedule(db, payload, company_id=company.id)
    intervals = schedule_service.list_intervals(db, company_id=company.id)
    return ScheduleConfigOut(
        skip_holidays=config.skip_holidays,
        enabled=config.enabled,
        disabled_by_dialer=config.disabled_by_dialer or False,
        wallet_balance=config.wallet_balance or 0,
        cost_per_connected=config.cost_per_connected or 0,
        version=config.version,
        updated_at=config.updated_at,
        intervals=[
            ScheduleInterval(day_of_week=i.day_of_week, start_time=i.start_time, end_time=i.end_time)
            for i in intervals
        ],
    )
