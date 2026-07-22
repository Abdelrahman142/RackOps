from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, get_db
from app.dependencies.rbac import RequireRole
from app.models.pdu import PDU
from app.models.rack import Rack
from app.models.ups import UPS
from app.schemas.dashboard import (
    CapacityForecast,
    CapacityOverview,
    CoolingDashboard,
    DashboardOverview,
    NetworkDashboard,
    PowerDashboard,
    PowerTrendPoint,
)
from app.services.dashboard import DashboardService

router = APIRouter(tags=["Dashboard & Analytics"])

WRITE_ROLES = ("OWNER", "ADMIN", "ENGINEER")
READ_ROLES = ("OWNER", "ADMIN", "ENGINEER", "VIEWER")


@router.get(
    "/dashboard/overview",
    response_model=DashboardOverview,
    summary="Get dashboard overview",
)
def get_overview(
    current_user=Depends(RequireRole(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_dashboard_overview(current_user.company_id)


@router.get(
    "/dashboard/power",
    response_model=PowerDashboard,
    summary="Get power dashboard",
)
def get_power_dashboard(
    current_user=Depends(RequireRole(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    company_id = current_user.company_id

    ups_cap_stmt = select(func.coalesce(func.sum(UPS.capacity_kva), 0.0)).where(
        UPS.company_id == company_id,
    )
    ups_capacity = float(db.execute(ups_cap_stmt).scalar_one())

    ups_count_stmt = select(func.count()).select_from(UPS).where(
        UPS.company_id == company_id,
    )
    ups_count = db.execute(ups_count_stmt).scalar_one()

    pdu_count_stmt = select(func.count()).select_from(PDU).where(
        PDU.company_id == company_id,
    )
    pdu_count = db.execute(pdu_count_stmt).scalar_one()

    rack_stmt = select(
        func.coalesce(func.sum(Rack.power_capacity_kw), 0.0),
        func.coalesce(func.sum(Rack.current_power_usage_kw), 0.0),
    ).where(
        Rack.company_id == company_id,
        Rack.deleted_at.is_(None),
    )
    r_row = db.execute(rack_stmt).one()
    p_cap = float(r_row[0])
    p_use = float(r_row[1])
    utilization = (p_use / p_cap * 100) if p_cap > 0 else None

    rack_details = service.get_rack_power_details(company_id)

    return PowerDashboard(
        ups_count=ups_count,
        pdu_count=pdu_count,
        total_ups_capacity_kva=ups_capacity,
        total_rack_power_capacity_kw=p_cap if p_cap > 0 else None,
        total_rack_power_usage_kw=p_use if p_cap > 0 else None,
        rack_utilization_percent=utilization,
        rack_power_details=rack_details,
    )


@router.get(
    "/dashboard/cooling",
    response_model=CoolingDashboard,
    summary="Get cooling dashboard",
)
def get_cooling_dashboard(
    current_user=Depends(RequireRole(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_cooling_dashboard(current_user.company_id)


@router.get(
    "/dashboard/network",
    response_model=NetworkDashboard,
    summary="Get network dashboard",
)
def get_network_dashboard(
    current_user=Depends(RequireRole(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_network_dashboard(current_user.company_id)


@router.get(
    "/dashboard/capacity",
    response_model=CapacityOverview,
    summary="Get capacity overview",
)
def get_capacity_overview(
    current_user=Depends(RequireRole(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_capacity_overview(current_user.company_id)


@router.get(
    "/dashboard/capacity/forecast",
    response_model=CapacityForecast,
    summary="Get capacity forecast",
)
def get_capacity_forecast(
    days_ahead: int = Query(30, ge=1, le=365),
    current_user=Depends(RequireRole(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_capacity_forecast(
        current_user.company_id, days_ahead
    )


@router.get(
    "/dashboard/power/trends",
    response_model=list[PowerTrendPoint],
    summary="Get power trends",
)
def get_power_trends(
    days: int = Query(7, ge=1, le=90),
    current_user=Depends(RequireRole(*READ_ROLES)),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_power_trends(current_user.company_id, days)
