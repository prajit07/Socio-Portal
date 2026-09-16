from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
oauth2_scheme_required = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Return the current user if a valid Bearer token is supplied, else None.

    Used by public endpoints (problem map / explorer) so guests can browse
    public problems without logging in.
    """
    if not token:
        return None
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
    except ValueError:
        return None
    return db.get(User, user_id)


def get_current_user(
    token: str = Depends(oauth2_scheme_required),
    db: Session = Depends(get_db),
) -> User:
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise creds_exc
    except ValueError:
        raise creds_exc

    user = db.get(User, user_id)
    if not user:
        raise creds_exc
    return user


def require_role(*allowed_roles: str):
    """Factory: returns a dependency that 403s when user.role not in allowed_roles."""

    allowed = set(allowed_roles)

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' is not permitted for this resource.",
            )
        return current_user

    return _checker