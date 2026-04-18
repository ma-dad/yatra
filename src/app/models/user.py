from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class UserType(str, enum.Enum):
    SEEKER = "seeker"
    VOLUNTEER = "volunteer"


class User(Base):
    """Base user model for both seekers and volunteers"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    google_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    user_type = Column(SQLEnum(UserType), nullable=False)
    
    # Profile information stored as JSON
    profile = Column(JSON, nullable=False)
    
    # Auth information
    refresh_token = Column(String, nullable=True)
    last_login = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships will be defined by specific user types


class Seeker(Base):
    """Seeker-specific model with relationship to seek requests"""
    __tablename__ = "seekers"
    
    user_id = Column(String, primary_key=True)
    
    # Relationship to seek requests
    seek_requests = relationship("SeekRequest", back_populates="seeker", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", 
                                   foreign_keys="CalendarEvent.user_id",
                                   primaryjoin="and_(Seeker.user_id==CalendarEvent.user_id, CalendarEvent.user_type=='seek')",
                                   back_populates="seeker")


class Volunteer(Base):
    """Volunteer-specific model with relationship to volunteer requests"""
    __tablename__ = "volunteers"
    
    user_id = Column(String, primary_key=True)
    
    # Relationship to volunteer requests
    volunteer_requests = relationship("VolunteerRequest", back_populates="volunteer", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent",
                                   foreign_keys="CalendarEvent.user_id", 
                                   primaryjoin="and_(Volunteer.user_id==CalendarEvent.user_id, CalendarEvent.user_type=='volunteer')",
                                   back_populates="volunteer")
