from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user, get_db
from app.dependencies.rbac import RequireRole
from app.models.user import User
from app.schemas.user import (
    ProfileUpdateRequest,
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.services.user import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    return service.get_profile(current_user.id)


@router.patch(
    "/me",
    response_model=UserResponse,
)
def update_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    return service.update_profile(
        user_id=current_user.id,
        name=data.name,
        current_password=data.current_password,
        new_password=data.new_password,
    )


@router.get(
    "",
    response_model=UserListResponse,
    dependencies=[
        Depends(
            RequireRole(
                "OWNER", "ADMIN", "ENGINEER", "VIEWER"
            )
        )
    ],
)
def list_users(
    current_user: User = Depends(
        RequireRole(
            "OWNER", "ADMIN", "ENGINEER", "VIEWER"
        )
    ),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    return service.list_users(current_user.company_id)


@router.post(
    "",
    response_model=UserResponse,
    dependencies=[
        Depends(RequireRole("OWNER", "ADMIN"))
    ],
)
def create_user(
    data: UserCreateRequest,
    current_user: User = Depends(
        RequireRole("OWNER", "ADMIN")
    ),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    return service.create_user(
        company_id=current_user.company_id,
        name=data.name,
        email=data.email,
        password=data.password,
        role=data.role,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[
        Depends(
            RequireRole(
                "OWNER", "ADMIN", "ENGINEER", "VIEWER"
            )
        )
    ],
)
def get_user(
    user_id: str,
    current_user: User = Depends(
        RequireRole(
            "OWNER", "ADMIN", "ENGINEER", "VIEWER"
        )
    ),
    db: Session = Depends(get_db),
):
    import uuid as _uuid

    service = UserService(db)
    return service.get_user(
        company_id=current_user.company_id,
        user_id=_uuid.UUID(user_id),
    )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[
        Depends(RequireRole("OWNER", "ADMIN"))
    ],
)
def update_user(
    user_id: str,
    data: UserUpdateRequest,
    current_user: User = Depends(
        RequireRole("OWNER", "ADMIN")
    ),
    db: Session = Depends(get_db),
):
    import uuid as _uuid

    service = UserService(db)
    return service.update_user(
        company_id=current_user.company_id,
        user_id=_uuid.UUID(user_id),
        name=data.name,
        role=data.role,
        acting_user_role=current_user.role,
    )


@router.delete(
    "/{user_id}",
    dependencies=[
        Depends(RequireRole("OWNER", "ADMIN"))
    ],
)
def delete_user(
    user_id: str,
    current_user: User = Depends(
        RequireRole("OWNER", "ADMIN")
    ),
    db: Session = Depends(get_db),
):
    import uuid as _uuid

    service = UserService(db)
    return service.delete_user(
        company_id=current_user.company_id,
        user_id=_uuid.UUID(user_id),
        acting_user_id=current_user.id,
        acting_user_role=current_user.role,
    )
