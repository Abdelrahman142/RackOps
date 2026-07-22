import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        company_id: uuid.UUID,
        name: str,
        email: str,
        password_hash: str,
        role: str = "VIEWER",
    ) -> User:
        user = User(
            company_id=company_id,
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
        )
        self.db.add(user)
        return user

    def get_by_id(
        self, user_id: uuid.UUID
    ) -> User | None:
        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    def get_by_email(
        self, email: str
    ) -> User | None:
        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

    def get_active_by_id(
        self, user_id: uuid.UUID
    ) -> User | None:
        return (
            self.db.query(User)
            .filter(
                User.id == user_id,
                User.deleted_at.is_(None),
            )
            .first()
        )

    def get_active_by_company(
        self, company_id: uuid.UUID
    ) -> list[User]:
        return (
            self.db.query(User)
            .filter(
                User.company_id == company_id,
                User.deleted_at.is_(None),
            )
            .order_by(User.created_at.desc())
            .all()
        )

    def count_active_by_company(
        self, company_id: uuid.UUID
    ) -> int:
        return (
            self.db.query(func.count(User.id))
            .filter(
                User.company_id == company_id,
                User.deleted_at.is_(None),
            )
            .scalar()
        )

    def get_active_by_company_and_id(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> User | None:
        return (
            self.db.query(User)
            .filter(
                User.id == user_id,
                User.company_id == company_id,
                User.deleted_at.is_(None),
            )
            .first()
        )

    def update(
        self,
        user: User,
        name: str | None = None,
        role: str | None = None,
        password_hash: str | None = None,
    ) -> User:
        if name is not None:
            user.name = name
        if role is not None:
            user.role = role
        if password_hash is not None:
            user.password_hash = password_hash
        self.db.flush()
        return user

    def soft_delete(self, user: User) -> User:
        user.deleted_at = datetime.utcnow()
        self.db.flush()
        return user
