from fastapi import Depends

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.utils.exceptions import AuthorizationException


class RequireRole:
    def __init__(self, *allowed_roles: str):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in self.allowed_roles:
            raise AuthorizationException(
                detail=(
                    f"Role '{current_user.role}' is not authorized "
                    f"for this action. Required: "
                    f"{', '.join(self.allowed_roles)}"
                )
            )
        return current_user
