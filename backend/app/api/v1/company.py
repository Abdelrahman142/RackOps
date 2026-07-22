from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.company import (
    CompanyResponse,
    CompanyUpdateRequest,
)
from app.services.company import CompanyService

router = APIRouter(
    prefix="/company",
    tags=["Company"],
)


@router.get(
    "",
    response_model=CompanyResponse,
    dependencies=[
        Depends(
            RequireRole(
                "OWNER", "ADMIN", "ENGINEER", "VIEWER"
            )
        )
    ],
)
def get_company(
    current_user: User = Depends(
        RequireRole(
            "OWNER", "ADMIN", "ENGINEER", "VIEWER"
        )
    ),
    db: Session = Depends(get_db),
):
    service = CompanyService(db)
    return service.get_company(current_user.company_id)


@router.patch(
    "",
    response_model=CompanyResponse,
    dependencies=[
        Depends(RequireRole("OWNER"))
    ],
)
def update_company(
    data: CompanyUpdateRequest,
    current_user: User = Depends(
        RequireRole("OWNER")
    ),
    db: Session = Depends(get_db),
):
    service = CompanyService(db)
    return service.update_company(
        company_id=current_user.company_id,
        name=data.name,
        email=data.email,
        country=data.country,
    )
