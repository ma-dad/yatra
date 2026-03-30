from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class RequestStatus(str, enum.Enum):
    ACTIVE = "active"
    MATCHED = "matched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SeekRequest(Base):
    """Model for assistance requests from seekers"""
    __tablename__ = "seek_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    seeker_id = Column(String, ForeignKey("seekers.user_id"), nullable=False)
    
    # Travel details stored as JSON
    travel_details = Column(JSON, nullable=False)
    
    # Assistance needed stored as JSON
    assistance_needed = Column(JSON, nullable=False)
    
    status = Column(SQLEnum(RequestStatus), default=RequestStatus.ACTIVE)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    seeker = relationship("Seeker", back_populates="seek_requests")
    matches = relationship("Match", foreign_keys="Match.seek_request_id", back_populates="seek_request")
    calendar_events = relationship("CalendarEvent", 
                                   foreign_keys="CalendarEvent.request_id",
                                   primaryjoin="and_(SeekRequest.id==CalendarEvent.request_id, CalendarEvent.event_type=='seek')",
                                   back_populates="seek_request")


class VolunteerRequest(Base):
    """Model for volunteer offers from helpers"""
    __tablename__ = "volunteer_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    volunteer_id = Column(String, ForeignKey("volunteers.user_id"), nullable=False)
    
    # Travel details stored as JSON
    travel_details = Column(JSON, nullable=False)
    
    # Assistance offered stored as JSON
    assistance_offered = Column(JSON, nullable=False)
    
    # Availability stored as JSON
    availability = Column(JSON, nullable=True)
    
    status = Column(SQLEnum(RequestStatus), default=RequestStatus.ACTIVE)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    volunteer = relationship("Volunteer", back_populates="volunteer_requests")
    matches = relationship("Match", foreign_keys="Match.volunteer_request_id", back_populates="volunteer_request")
    calendar_events = relationship("CalendarEvent",
                                   foreign_keys="CalendarEvent.request_id",
                                   primaryjoin="and_(VolunteerRequest.id==CalendarEvent.request_id, CalendarEvent.event_type=='volunteer')",
                                   back_populates="volunteer_request")
