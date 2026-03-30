from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from app.schemas.user import UserType, SeekerProfile, VolunteerProfile


class GoogleAuthRequest(BaseModel):
    google_token: str
    user_type: UserType
    profile: Optional[SeekerProfile | VolunteerProfile] = None


class DevLoginRequest(BaseModel):
    """Dev/test login request - only available when ENABLE_GOOGLE_AUTH is False."""
    email: EmailStr
    name: Optional[str] = None
    user_type: UserType = UserType.SEEKER


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    success: bool
    data: Dict
    message: str


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[EmailStr] = None
    user_type: Optional[UserType] = None
