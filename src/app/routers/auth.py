from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import GoogleAuthRequest, DevLoginRequest, AuthResponse, Token
from app.schemas.user import UserType
from app.models.user import User, Seeker, Volunteer
from app.utils.auth import verify_google_token, create_access_token
from app.config import settings
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def _ensure_seeker_volunteer_records(user: User, db: Session):
    """Create Seeker and Volunteer records for a user if they do not exist yet.

    Every user can act as both a seeker and a volunteer, so both records are
    created on first login.
    """
    if not db.query(Seeker).filter(Seeker.user_id == user.id).first():
        db.add(Seeker(user_id=user.id))
    if not db.query(Volunteer).filter(Volunteer.user_id == user.id).first():
        db.add(Volunteer(user_id=user.id))


@router.post("/google", response_model=AuthResponse)
async def google_auth(
    auth_request: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with Google OAuth token.
    Only available when ENABLE_GOOGLE_AUTH=true.
    Creates new user if not exists, returns JWT token.
    """

    if not settings.ENABLE_GOOGLE_AUTH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google authentication is disabled. Use /api/auth/dev-login for testing."
        )

    google_user = verify_google_token(auth_request.google_token)
    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google token"
        )

    user = db.query(User).filter(User.google_id == google_user['google_id']).first()
    is_new_user = False

    if not user:
        is_new_user = True

        profile = {
            "name": google_user['name'],
            "google_picture": google_user.get('picture'),
            "preferred_language": "en"
        }
        if auth_request.profile:
            profile.update(auth_request.profile.model_dump(exclude_none=True))

        user = User(
            google_id=google_user['google_id'],
            email=google_user['email'],
            user_type=auth_request.user_type,
            profile=profile,
            last_login=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        db.add(user)
        db.flush()
        _ensure_seeker_volunteer_records(user, db)
        db.commit()
        db.refresh(user)
        logger.info(f"Created new user: {user.id} ({user.email})")
    else:
        user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
        _ensure_seeker_volunteer_records(user, db)
        db.commit()
        logger.info(f"User logged in: {user.id} ({user.email})")

    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "user_type": user.user_type.value
        }
    )

    return AuthResponse(
        success=True,
        data={
            "user_id": user.id,
            "email": user.email,
            "user_type": user.user_type.value,
            "is_new_user": is_new_user,
            "token": access_token,
            "profile": user.profile
        },
        message="Authentication successful"
    )


@router.post("/dev-login", response_model=AuthResponse)
async def dev_login(
    login_request: DevLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Development / testing login endpoint.

    Allows creating or retrieving a user by e-mail address without a real
    Google OAuth token.  This endpoint is **only available** when the
    ``ENABLE_GOOGLE_AUTH`` configuration flag is ``False`` (the default).
    Disable it in production by setting ENABLE_GOOGLE_AUTH=true.
    """

    if settings.ENABLE_GOOGLE_AUTH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev login is disabled when ENABLE_GOOGLE_AUTH=true. Use /api/auth/google."
        )

    user = db.query(User).filter(User.email == login_request.email).first()
    is_new_user = False

    if not user:
        is_new_user = True
        profile = {
            "name": login_request.name or login_request.email.split("@")[0],
            "preferred_language": "en"
        }
        # Use the email as a synthetic google_id so the column constraint is met
        user = User(
            google_id=f"dev:{login_request.email}",
            email=login_request.email,
            user_type=login_request.user_type,
            profile=profile,
            last_login=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        db.add(user)
        db.flush()
        _ensure_seeker_volunteer_records(user, db)
        db.commit()
        db.refresh(user)
        logger.info(f"Dev login: created user {user.id} ({user.email})")
    else:
        user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
        _ensure_seeker_volunteer_records(user, db)
        db.commit()
        logger.info(f"Dev login: user {user.id} ({user.email})")

    access_token = create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "user_type": user.user_type.value
        }
    )

    return AuthResponse(
        success=True,
        data={
            "user_id": user.id,
            "email": user.email,
            "user_type": user.user_type.value,
            "is_new_user": is_new_user,
            "token": access_token,
            "profile": user.profile
        },
        message="Dev login successful"
    )


@router.post("/logout")
async def logout():
    """Logout endpoint (for future token invalidation)"""
    return {"message": "Logged out successfully"}
