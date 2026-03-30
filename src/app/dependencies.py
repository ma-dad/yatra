from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.auth import verify_token
from app.models.user import User, Seeker, Volunteer
from app.schemas.auth import TokenData

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_seeker(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Return the current user, ensuring they have a Seeker record.

    Because a user can hold both the seeker and volunteer roles, we check for
    the existence of a Seeker row rather than inspecting user_type.  If the
    row is missing it is created automatically so that existing users are not
    locked out.
    """
    seeker = db.query(Seeker).filter(Seeker.user_id == current_user.id).first()
    if not seeker:
        db.add(Seeker(user_id=current_user.id))
        db.commit()
    return current_user


def get_current_volunteer(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Return the current user, ensuring they have a Volunteer record.

    Because a user can hold both the seeker and volunteer roles, we check for
    the existence of a Volunteer row rather than inspecting user_type.  If the
    row is missing it is created automatically so that existing users are not
    locked out.
    """
    volunteer = db.query(Volunteer).filter(Volunteer.user_id == current_user.id).first()
    if not volunteer:
        db.add(Volunteer(user_id=current_user.id))
        db.commit()
    return current_user
