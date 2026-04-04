from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    SEEK = "seek"
    VOLUNTEER = "volunteer"


class CalendarEventCreate(BaseModel):
    user_id: str
    user_type: EventType
    request_id: str
    event_type: EventType
    title: str
    travel_details: Dict


class CalendarEventResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: str
    user_id: str
    user_type: str
    request_id: str
    event_type: str
    title: str
    travel_details: dict
    is_public: bool
    created_at: datetime
    updated_at: datetime
