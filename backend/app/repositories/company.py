import uuid

from sqlalchemy.orm import Session

from app.models.company import Company


class CompanyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        slug: str,
        email: str,
        country: str | None = None,
    ) -> Company:
        company = Company(
            name=name,
            slug=slug,
            email=email,
            country=country,
        )
        self.db.add(company)
        self.db.flush()
        return company

    def get_by_id(
        self, company_id: uuid.UUID
    ) -> Company | None:
        return (
            self.db.query(Company)
            .filter(Company.id == company_id)
            .first()
        )

    def get_by_slug(self, slug: str) -> Company | None:
        return (
            self.db.query(Company)
            .filter(Company.slug == slug)
            .first()
        )

    def get_by_email(
        self, email: str
    ) -> Company | None:
        return (
            self.db.query(Company)
            .filter(Company.email == email)
            .first()
        )

    def update(
        self,
        company: Company,
        name: str | None = None,
        email: str | None = None,
        country: str | None = None,
    ) -> Company:
        if name is not None:
            company.name = name
        if email is not None:
            company.email = email
        if country is not None:
            company.country = country
        self.db.flush()
        return company
