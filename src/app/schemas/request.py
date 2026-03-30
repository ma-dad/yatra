from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RequestStatus(str, Enum):
    ACTIVE = "active"
    MATCHED = "matched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Layover(BaseModel):
    has_layover: bool = False
    layover_airport: Optional[str] = None
    layover_duration: Optional[int] = None  # in minutes


class TravelDetails(BaseModel):
    travel_time: datetime
    source_airport: str = Field(..., description="IATA airport code")
    destination_airport: str = Field(..., description="IATA airport code")
    airline: Optional[str] = None
    flight_number: str
    number_of_people: int = 1
    layover: Optional[Layover] = None
    seat_number: Optional[str] = None


class AssistanceNeeded(BaseModel):
    type: str = "travel_companion"
    categories: List[str] = Field(default_factory=list)
    special_requirements: List[str] = Field(default_factory=list)
    comments: Optional[str] = None


class AssistanceOffered(BaseModel):
    types: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    comments: Optional[str] = None


class Availability(BaseModel):
    flexible_timing: bool = False
    time_buffer: Optional[int] = None  # in minutes


# Seek Request Schemas
class SeekRequestCreate(BaseModel):
    travel_details: TravelDetails
    assistance_needed: AssistanceNeeded


class SeekRequestUpdate(BaseModel):
    travel_details: Optional[TravelDetails] = None
    assistance_needed: Optional[AssistanceNeeded] = None
    status: Optional[RequestStatus] = None


class SeekRequestResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: str
    seeker_id: str
    travel_details: dict
    assistance_needed: dict
    status: RequestStatus
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


# Volunteer Request Schemas
class VolunteerRequestCreate(BaseModel):
    travel_details: TravelDetails
    assistance_offered: AssistanceOffered
    availability: Optional[Availability] = None


class VolunteerRequestUpdate(BaseModel):
    travel_details: Optional[TravelDetails] = None
    assistance_offered: Optional[AssistanceOffered] = None
    availability: Optional[Availability] = None
    status: Optional[RequestStatus] = None


class VolunteerRequestResponse(BaseModel):
    model_config = {"from_attributes": True}
    
    id: str
    volunteer_id: str
    travel_details: dict
    assistance_offered: dict
    availability: Optional[dict] = None
    status: RequestStatus
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
