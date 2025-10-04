from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import GoogleAuthRequest, AuthResponse, Token
from app.schemas.user import UserType
from app.models.user import User, Seeker, Volunteer
from app.utils.auth import verify_google_token, create_access_token
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/google", response_model=AuthResponse)
async def google_auth(
    auth_request: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with Google OAuth token
    Creates new user if not exists, returns JWT token
    """
    
    # Verify Google token
    google_user = verify_google_token(auth_request.google_token)
    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google token"
        )
    
    # Check if user exists
    user = db.query(User).filter(User.google_id == google_user['google_id']).first()
    is_new_user = False
    
    if not user:
        # Create new user
        is_new_user = True
        
        # Build profile from Google data and request data
        profile = {
            "name": google_user['name'],
            "google_picture": google_user.get('picture'),
            "preferred_language": "en"
        }
        
        # Add profile data from request if provided
        if auth_request.profile:
            profile.update(auth_request.profile.model_dump(exclude_none=True))
        
        user = User(
            google_id=google_user['google_id'],
            email=google_user['email'],
            user_type=auth_request.user_type,
            profile=profile,
            last_login=datetime.utcnow()
        )
        db.add(user)
        db.flush()  # Get the user ID
        
        # Create seeker or volunteer entry
        if auth_request.user_type == UserType.SEEKER:
            seeker = Seeker(user_id=user.id)
            db.add(seeker)
        else:
            volunteer = Volunteer(user_id=user.id)
            db.add(volunteer)
        
        db.commit()
        db.refresh(user)
        logger.info(f"Created new user: {user.id} ({user.email})")
    else:
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        logger.info(f"User logged in: {user.id} ({user.email})")
    
    # Create JWT token
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


@router.post("/logout")
async def logout(db: Session = Depends(get_db)):
    """Logout endpoint (for future token invalidation)"""
    return {"message": "Logged out successfully"}
