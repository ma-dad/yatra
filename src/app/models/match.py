from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class MatchStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Match(Base):
    """Model for matches between seek and volunteer requests"""
    __tablename__ = "matches"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    seek_request_id = Column(String, ForeignKey("seek_requests.id"), nullable=False)
    volunteer_request_id = Column(String, ForeignKey("volunteer_requests.id"), nullable=False)
    
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.PENDING)
    match_score = Column(Float, nullable=False)  # Match indicator; currently stored as 1.0 for all matches
    
    # Communication details stored as JSON
    communication = Column(JSON, nullable=True)
    
    # Completion details stored as JSON
    completion = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    seek_request = relationship("SeekRequest", back_populates="matches", foreign_keys=[seek_request_id])
    volunteer_request = relationship("VolunteerRequest", back_populates="matches", foreign_keys=[volunteer_request_id])
