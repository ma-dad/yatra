from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.dependencies import get_current_user, get_current_seeker, get_current_volunteer
from app.models.user import User
from app.models.request import SeekRequest, VolunteerRequest, RequestStatus
from app.models.calendar import CalendarEvent, EventType
from app.schemas.request import (
    SeekRequestCreate, SeekRequestUpdate, SeekRequestResponse,
    VolunteerRequestCreate, VolunteerRequestUpdate, VolunteerRequestResponse
)
from app.services.matching_service import MatchingService
from app.utils.email import send_match_notification
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
matching_service = MatchingService()


# Seek Request Endpoints
@router.post("/seek", response_model=SeekRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_seek_request(
    request_data: SeekRequestCreate,
    current_user: User = Depends(get_current_seeker),
    db: Session = Depends(get_db)
):
    """Create a new seek request (seeker only)"""
    
    # Calculate expiration (travel time + 24 hours)
    travel_time = request_data.travel_details.travel_time
    expires_at = travel_time + timedelta(hours=24)
    
    # Create seek request
    seek_request = SeekRequest(
        seeker_id=current_user.id,
        travel_details=request_data.travel_details.model_dump(),
        assistance_needed=request_data.assistance_needed.model_dump(),
        expires_at=expires_at
    )
    db.add(seek_request)
    db.flush()
    
    # Create calendar event
    calendar_event = CalendarEvent(
        user_id=current_user.id,
        user_type=EventType.SEEK,
        request_id=seek_request.id,
        event_type=EventType.SEEK,
        title=f"Seek Help: {request_data.travel_details.source_airport} → {request_data.travel_details.destination_airport}",
        travel_details=request_data.travel_details.model_dump()
    )
    db.add(calendar_event)
    db.commit()
    db.refresh(seek_request)
    
    # Find matches
    matches = matching_service.find_matches(seek_request.id, db)
    logger.info(f"Created seek request {seek_request.id}, found {len(matches)} potential matches")
    
    return seek_request


@router.get("/seek", response_model=List[SeekRequestResponse])
async def list_seek_requests(
    status: Optional[RequestStatus] = Query(None),
    current_user: User = Depends(get_current_seeker),
    db: Session = Depends(get_db)
):
    """List all seek requests for current seeker"""
    
    query = db.query(SeekRequest).filter(SeekRequest.seeker_id == current_user.id)
    
    if status:
        query = query.filter(SeekRequest.status == status)
    
    requests = query.order_by(SeekRequest.created_at.desc()).all()
    return requests


@router.get("/seek/{request_id}", response_model=SeekRequestResponse)
async def get_seek_request(
    request_id: str,
    current_user: User = Depends(get_current_seeker),
    db: Session = Depends(get_db)
):
    """Get a specific seek request"""
    
    seek_request = db.query(SeekRequest).filter(
        SeekRequest.id == request_id,
        SeekRequest.seeker_id == current_user.id
    ).first()
    
    if not seek_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seek request not found"
        )
    
    return seek_request


@router.put("/seek/{request_id}", response_model=SeekRequestResponse)
async def update_seek_request(
    request_id: str,
    update_data: SeekRequestUpdate,
    current_user: User = Depends(get_current_seeker),
    db: Session = Depends(get_db)
):
    """Update a seek request"""
    
    seek_request = db.query(SeekRequest).filter(
        SeekRequest.id == request_id,
        SeekRequest.seeker_id == current_user.id
    ).first()
    
    if not seek_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seek request not found"
        )
    
    # Update fields
    if update_data.travel_details:
        seek_request.travel_details = update_data.travel_details.model_dump()
    if update_data.assistance_needed:
        seek_request.assistance_needed = update_data.assistance_needed.model_dump()
    if update_data.status:
        seek_request.status = update_data.status
    
    db.commit()
    db.refresh(seek_request)
    
    return seek_request


@router.delete("/seek/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seek_request(
    request_id: str,
    current_user: User = Depends(get_current_seeker),
    db: Session = Depends(get_db)
):
    """Delete a seek request"""
    
    seek_request = db.query(SeekRequest).filter(
        SeekRequest.id == request_id,
        SeekRequest.seeker_id == current_user.id
    ).first()
    
    if not seek_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seek request not found"
        )
    
    db.delete(seek_request)
    db.commit()
    
    return None


# Volunteer Request Endpoints
@router.post("/volunteer", response_model=VolunteerRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_volunteer_request(
    request_data: VolunteerRequestCreate,
    current_user: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db)
):
    """Create a new volunteer request (volunteer only)"""
    
    # Calculate expiration (travel time + 24 hours)
    travel_time = request_data.travel_details.travel_time
    expires_at = travel_time + timedelta(hours=24)
    
    # Create volunteer request
    volunteer_request = VolunteerRequest(
        volunteer_id=current_user.id,
        travel_details=request_data.travel_details.model_dump(),
        assistance_offered=request_data.assistance_offered.model_dump(),
        availability=request_data.availability.model_dump() if request_data.availability else None,
        expires_at=expires_at
    )
    db.add(volunteer_request)
    db.flush()
    
    # Create calendar event
    calendar_event = CalendarEvent(
        user_id=current_user.id,
        user_type=EventType.VOLUNTEER,
        request_id=volunteer_request.id,
        event_type=EventType.VOLUNTEER,
        title=f"Volunteer: {request_data.travel_details.source_airport} → {request_data.travel_details.destination_airport}",
        travel_details=request_data.travel_details.model_dump()
    )
    db.add(calendar_event)
    db.commit()
    db.refresh(volunteer_request)
    
    logger.info(f"Created volunteer request {volunteer_request.id}")
    
    return volunteer_request


@router.get("/volunteer", response_model=List[VolunteerRequestResponse])
async def list_volunteer_requests(
    status: Optional[RequestStatus] = Query(None),
    current_user: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db)
):
    """List all volunteer requests for current volunteer"""
    
    query = db.query(VolunteerRequest).filter(VolunteerRequest.volunteer_id == current_user.id)
    
    if status:
        query = query.filter(VolunteerRequest.status == status)
    
    requests = query.order_by(VolunteerRequest.created_at.desc()).all()
    return requests


@router.get("/volunteer/{request_id}", response_model=VolunteerRequestResponse)
async def get_volunteer_request(
    request_id: str,
    current_user: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db)
):
    """Get a specific volunteer request"""
    
    volunteer_request = db.query(VolunteerRequest).filter(
        VolunteerRequest.id == request_id,
        VolunteerRequest.volunteer_id == current_user.id
    ).first()
    
    if not volunteer_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer request not found"
        )
    
    return volunteer_request


@router.put("/volunteer/{request_id}", response_model=VolunteerRequestResponse)
async def update_volunteer_request(
    request_id: str,
    update_data: VolunteerRequestUpdate,
    current_user: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db)
):
    """Update a volunteer request"""
    
    volunteer_request = db.query(VolunteerRequest).filter(
        VolunteerRequest.id == request_id,
        VolunteerRequest.volunteer_id == current_user.id
    ).first()
    
    if not volunteer_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer request not found"
        )
    
    # Update fields
    if update_data.travel_details:
        volunteer_request.travel_details = update_data.travel_details.model_dump()
    if update_data.assistance_offered:
        volunteer_request.assistance_offered = update_data.assistance_offered.model_dump()
    if update_data.availability:
        volunteer_request.availability = update_data.availability.model_dump()
    if update_data.status:
        volunteer_request.status = update_data.status
    
    db.commit()
    db.refresh(volunteer_request)
    
    return volunteer_request


@router.delete("/volunteer/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_volunteer_request(
    request_id: str,
    current_user: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db)
):
    """Delete a volunteer request"""
    
    volunteer_request = db.query(VolunteerRequest).filter(
        VolunteerRequest.id == request_id,
        VolunteerRequest.volunteer_id == current_user.id
    ).first()
    
    if not volunteer_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer request not found"
        )
    
    db.delete(volunteer_request)
    db.commit()
    
    return None
