import uuid

from sqlalchemy.orm import Session

from app.repositories.company import CompanyRepository
from app.repositories.user import UserRepository
from app.utils.exceptions import (
    DuplicateException,
    NotFoundException,
)


class CompanyService:
    def __init__(self, db: Session):
        self.db = db
        self.company_repo = CompanyRepository(db)
        self.user_repo = UserRepository(db)

    def get_company(
        self, company_id: uuid.UUID
    ) -> dict:
        company = self.company_repo.get_by_id(
            company_id
        )

        if not company:
            raise NotFoundException(
                detail="Company not found"
            )

        return {
            "id": str(company.id),
            "name": company.name,
            "slug": company.slug,
            "email": company.email,
            "country": company.country,
            "created_at": company.created_at.isoformat(),
            "updated_at": company.updated_at.isoformat(),
        }

    def update_company(
        self,
        company_id: uuid.UUID,
        name: str | None = None,
        email: str | None = None,
        country: str | None = None,
    ) -> dict:
        company = self.company_repo.get_by_id(
            company_id
        )

        if not company:
            raise NotFoundException(
                detail="Company not found"
            )

        if email is not None:
            existing = self.company_repo.get_by_email(
                email
            )
            if existing and existing.id != company.id:
                raise DuplicateException(
                    detail=(
                        "A company with this email "
                        "already exists"
                    )
                )

        company = self.company_repo.update(
            company,
            name=name,
            email=email,
            country=country,
        )

        self.db.commit()
        self.db.refresh(company)

        return {
            "id": str(company.id),
            "name": company.name,
            "slug": company.slug,
            "email": company.email,
            "country": company.country,
            "created_at": company.created_at.isoformat(),
            "updated_at": company.updated_at.isoformat(),
        }
