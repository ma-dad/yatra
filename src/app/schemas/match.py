from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
from enum import Enum


class MatchStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchCreate(BaseModel):
    seek_request_id: str
    volunteer_request_id: str
    match_score: float


class MatchUpdate(BaseModel):
    status: Optional[MatchStatus] = None
    communication: Optional[Dict] = None
    completion: Optional[Dict] = None


class MatchResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: str
    seek_request_id: str
    volunteer_request_id: str
    status: MatchStatus
    match_score: float
    communication: Optional[dict] = None
    completion: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class MatchWithDetails(BaseModel):
    model_config = {"from_attributes": True}
    
    match_id: str
    compatibility_score: float
    request: dict
    user: dict
    created_at: datetime
