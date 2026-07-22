import re
import uuid

from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.repositories.company import CompanyRepository
from app.repositories.user import UserRepository
from app.utils.exceptions import (
    AuthenticationException,
    DuplicateException,
)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.company_repo = CompanyRepository(db)
        self.user_repo = UserRepository(db)

    def _generate_slug(self, name: str) -> str:
        slug = name.lower().strip()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")
        return slug

    def register(
        self,
        company_name: str,
        company_email: str,
        name: str,
        email: str,
        password: str,
        country: str | None = None,
    ) -> dict:
        slug = self._generate_slug(company_name)

        if self.company_repo.get_by_slug(slug):
            raise DuplicateException(
                detail="A company with this name already exists"
            )

        if self.company_repo.get_by_email(company_email):
            raise DuplicateException(
                detail="A company with this email already exists"
            )

        if self.user_repo.get_by_email(email):
            raise DuplicateException(
                detail="A user with this email already exists"
            )

        company = self.company_repo.create(
            name=company_name,
            slug=slug,
            email=company_email,
            country=country,
        )

        user = self.user_repo.create(
            company_id=company.id,
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="OWNER",
        )

        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(company)

        return {"user": user, "company": company}

    def login(self, email: str, password: str) -> dict:
        user = self.user_repo.get_by_email(email)

        if not user or not verify_password(
            password, user.password_hash
        ):
            raise AuthenticationException(
                detail="Invalid email or password"
            )

        token = create_access_token(
            data={
                "sub": str(user.id),
                "company_id": str(user.company_id),
                "role": user.role,
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    def get_current_user(
        self, user_id: uuid.UUID
    ):
        user = self.user_repo.get_by_id(user_id)

        if not user:
            raise AuthenticationException(
                detail="User not found"
            )

        return user
