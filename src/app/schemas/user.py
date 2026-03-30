from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserType(str, Enum):
    SEEKER = "seeker"
    VOLUNTEER = "volunteer"


class EmergencyContact(BaseModel):
    name: str
    phone: str
    email: EmailStr


class SeekerProfile(BaseModel):
    name: str
    google_picture: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: str
    emergency_contact: EmergencyContact


class VolunteerProfile(BaseModel):
    name: str
    google_picture: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: str
    languages_spoken: List[str] = Field(default_factory=list)
    experience_level: Optional[str] = "beginner"
    specialties: List[str] = Field(default_factory=list)
    emergency_contact: Optional[EmergencyContact] = None


class UserCreate(BaseModel):
    google_id: str
    email: EmailStr
    user_type: UserType
    profile: SeekerProfile | VolunteerProfile


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: str
    email: EmailStr
    user_type: UserType
    profile: dict
    created_at: datetime
    updated_at: datetime
