import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.user import User
from app.utils.exceptions import AuthenticationException

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise AuthenticationException(
                detail="Invalid token"
            )
    except JWTError:
        raise AuthenticationException(
            detail="Invalid token"
        )

    user = db.query(User).filter(
        User.id == uuid.UUID(user_id)
    ).first()

    if user is None:
        raise AuthenticationException(
            detail="User not found"
        )

    return user
