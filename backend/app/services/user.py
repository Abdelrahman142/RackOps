import uuid

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.repositories.user import UserRepository
from app.utils.exceptions import (
    AuthenticationException,
    DuplicateException,
    NotFoundException,
    ValidationException,
)

VALID_ROLES = {"OWNER", "ADMIN", "ENGINEER", "VIEWER"}


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def list_users(
        self, company_id: uuid.UUID
    ) -> dict:
        users = self.user_repo.get_active_by_company(
            company_id
        )
        total = self.user_repo.count_active_by_company(
            company_id
        )

        return {
            "users": [
                {
                    "id": str(u.id),
                    "name": u.name,
                    "email": u.email,
                    "role": u.role,
                    "company_id": str(u.company_id),
                    "created_at": u.created_at.isoformat(),
                    "updated_at": u.updated_at.isoformat(),
                }
                for u in users
            ],
            "total": total,
        }

    def get_user(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        user = (
            self.user_repo.get_active_by_company_and_id(
                company_id, user_id
            )
        )

        if not user:
            raise NotFoundException(
                detail="User not found"
            )

        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "company_id": str(user.company_id),
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }

    def create_user(
        self,
        company_id: uuid.UUID,
        name: str,
        email: str,
        password: str,
        role: str = "VIEWER",
    ) -> dict:
        if role not in VALID_ROLES:
            raise ValidationException(
                detail=(
                    f"Invalid role: {role}. "
                    f"Must be one of: "
                    f"{', '.join(sorted(VALID_ROLES))}"
                )
            )

        if self.user_repo.get_by_email(email):
            raise DuplicateException(
                detail=(
                    "A user with this email "
                    "already exists"
                )
            )

        user = self.user_repo.create(
            company_id=company_id,
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=role,
        )

        self.db.commit()
        self.db.refresh(user)

        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "company_id": str(user.company_id),
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }

    def update_user(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str | None = None,
        role: str | None = None,
        acting_user_role: str | None = None,
    ) -> dict:
        user = (
            self.user_repo.get_active_by_company_and_id(
                company_id, user_id
            )
        )

        if not user:
            raise NotFoundException(
                detail="User not found"
            )

        if role is not None:
            if role not in VALID_ROLES:
                raise ValidationException(
                    detail=(
                        f"Invalid role: {role}. "
                        f"Must be one of: "
                        f"{', '.join(sorted(VALID_ROLES))}"
                    )
                )

            if (
                acting_user_role == "ADMIN"
                and user.role == "OWNER"
            ):
                raise ValidationException(
                    detail=(
                        "Admins cannot change the "
                        "role of an Owner"
                    )
                )

        self.user_repo.update(
            user, name=name, role=role
        )
        self.db.commit()
        self.db.refresh(user)

        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "company_id": str(user.company_id),
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }

    def delete_user(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        acting_user_id: uuid.UUID,
        acting_user_role: str,
    ) -> dict:
        user = (
            self.user_repo.get_active_by_company_and_id(
                company_id, user_id
            )
        )

        if not user:
            raise NotFoundException(
                detail="User not found"
            )

        if user.id == acting_user_id:
            raise ValidationException(
                detail=(
                    "You cannot delete your own account"
                )
            )

        if (
            acting_user_role == "ADMIN"
            and user.role == "OWNER"
        ):
            raise ValidationException(
                detail=(
                    "Admins cannot delete an Owner"
                )
            )

        self.user_repo.soft_delete(user)
        self.db.commit()

        return {
            "message": "User deleted successfully"
        }

    def get_profile(
        self, user_id: uuid.UUID
    ) -> dict:
        user = self.user_repo.get_active_by_id(
            user_id
        )

        if not user:
            raise AuthenticationException(
                detail="User not found"
            )

        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "company_id": str(user.company_id),
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }

    def update_profile(
        self,
        user_id: uuid.UUID,
        name: str | None = None,
        current_password: str | None = None,
        new_password: str | None = None,
    ) -> dict:
        user = self.user_repo.get_by_id(user_id)

        if not user:
            raise AuthenticationException(
                detail="User not found"
            )

        if new_password is not None:
            if current_password is None:
                raise ValidationException(
                    detail=(
                        "Current password is required "
                        "to set a new password"
                    )
                )

            if not verify_password(
                current_password, user.password_hash
            ):
                raise AuthenticationException(
                    detail="Current password is incorrect"
                )

            self.user_repo.update(
                user,
                name=name,
                password_hash=hash_password(
                    new_password
                ),
            )
        else:
            self.user_repo.update(user, name=name)

        self.db.commit()
        self.db.refresh(user)

        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "company_id": str(user.company_id),
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        }
