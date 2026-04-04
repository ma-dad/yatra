from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class EventType(str, enum.Enum):
    SEEK = "seek"
    VOLUNTEER = "volunteer"


class CalendarEvent(Base):
    """Model for calendar events representing travel plans"""
    __tablename__ = "calendar_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    user_type = Column(SQLEnum(EventType), nullable=False)
    request_id = Column(String, nullable=False)
    event_type = Column(SQLEnum(EventType), nullable=False)
    
    title = Column(String, nullable=False)
    
    # Travel details stored as JSON
    travel_details = Column(JSON, nullable=False)
    
    # Event visibility and metadata
    is_public = Column(Boolean, default=True)  # For future privacy controls
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - Note: These use string-based foreign keys for flexibility
    seeker = relationship("Seeker", 
                         foreign_keys=[user_id],
                         primaryjoin="and_(CalendarEvent.user_id==Seeker.user_id, CalendarEvent.user_type=='seek')",
                         back_populates="calendar_events", viewonly=True)
    
    volunteer = relationship("Volunteer",
                            foreign_keys=[user_id],
                            primaryjoin="and_(CalendarEvent.user_id==Volunteer.user_id, CalendarEvent.user_type=='volunteer')",
                            back_populates="calendar_events", viewonly=True)
    
    seek_request = relationship("SeekRequest",
                               foreign_keys=[request_id],
                               primaryjoin="and_(CalendarEvent.request_id==SeekRequest.id, CalendarEvent.event_type=='seek')",
                               back_populates="calendar_events", viewonly=True)
    
    volunteer_request = relationship("VolunteerRequest",
                                    foreign_keys=[request_id],
                                    primaryjoin="and_(CalendarEvent.request_id==VolunteerRequest.id, CalendarEvent.event_type=='volunteer')",
                                    back_populates="calendar_events", viewonly=True)
