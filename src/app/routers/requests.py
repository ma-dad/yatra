from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.dependencies import get_current_user, get_current_seeker, get_current_volunteer
from app.models.user import User
from app.models.request import SeekRequest, VolunteerRequest, RequestStatus
from app.models.match import Match, MatchStatus
from app.models.calendar import CalendarEvent, EventType
from app.schemas.request import (
    SeekRequestCreate, SeekRequestUpdate, SeekRequestResponse,
    VolunteerRequestCreate, VolunteerRequestUpdate, VolunteerRequestResponse
)
from app.services.matching_service import MatchingService
from app.utils.email import send_match_notification, send_email
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
matching_service = MatchingService()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _auto_expire_requests(db: Session):
    """Mark requests whose travel time has passed as EXPIRED."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for Model in (SeekRequest, VolunteerRequest):
        expired = db.query(Model).filter(
            Model.status == RequestStatus.ACTIVE,
            Model.expires_at <= now
        ).all()
        for req in expired:
            req.status = RequestStatus.EXPIRED
            logger.info("Auto-expired request %s (expires_at=%s)", req.id, req.expires_at)
    db.commit()


def _notify_volunteers_on_seek_cancel(seek_request: SeekRequest, db: Session):
    """Send cancellation notice to volunteers with ACCEPTED matches."""
    accepted_matches = db.query(Match).filter(
        Match.seek_request_id == seek_request.id,
        Match.status == MatchStatus.ACCEPTED
    ).all()

    for match in accepted_matches:
        match.status = MatchStatus.CANCELLED
        # Fetch volunteer user
        vol_req = db.query(VolunteerRequest).filter(
            VolunteerRequest.id == match.volunteer_request_id
        ).first()
        if vol_req:
            vol_user = db.query(User).filter(User.id == vol_req.volunteer_id).first()
            if vol_user:
                travel = seek_request.travel_details
                body = (
                    f"Hello,\n\n"
                    f"The seeker has cancelled a travel request that you had agreed to assist with.\n\n"
                    f"Travel Details:\n"
                    f"- Route: {travel.get('source_airport', 'N/A')} → {travel.get('destination_airport', 'N/A')}\n"
                    f"- Flight: {travel.get('flight_number', 'N/A')}\n"
                    f"- Date: {travel.get('travel_time', 'N/A')}\n\n"
                    f"Thank you for your willingness to help!\n\n"
                    f"Best regards,\nYatra Team"
                )
                send_email(
                    [vol_user.email],
                    "Seek Request Cancelled - Yatra",
                    body
                )
    db.commit()


# ---------------------------------------------------------------------------
# Seek Request Endpoints
# ---------------------------------------------------------------------------

@router.post("/seek", response_model=SeekRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_seek_request(
    request_data: SeekRequestCreate,
    current_user: User = Depends(get_current_seeker),
    db: Session = Depends(get_db)
):
    """Create a new seek request.

    A user may have at most SEEKER_REQUEST_LIMIT active seek requests at once.
    Creating the request automatically triggers matching against all active
    volunteer requests.
    """
    _auto_expire_requests(db)

    # Enforce per-user request limit
    active_count = db.query(SeekRequest).filter(
        SeekRequest.seeker_id == current_user.id,
        SeekRequest.status == RequestStatus.ACTIVE
    ).count()
    if active_count >= settings.SEEKER_REQUEST_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"You have reached the maximum of {settings.SEEKER_REQUEST_LIMIT} active seek requests."
        )

    travel_time = request_data.travel_details.travel_time
    expires_at = travel_time + timedelta(hours=24)

    seek_request = SeekRequest(
        seeker_id=current_user.id,
        travel_details=request_data.travel_details.model_dump(mode="json"),
        assistance_needed=request_data.assistance_needed.model_dump(mode="json"),
        expires_at=expires_at
    )
    db.add(seek_request)
    db.flush()

    calendar_event = CalendarEvent(
        user_id=current_user.id,
        user_type=EventType.SEEK,
        request_id=seek_request.id,
        event_type=EventType.SEEK,
        title=f"Seek Help: {request_data.travel_details.source_airport} → {request_data.travel_details.destination_airport}",
        travel_details=request_data.travel_details.model_dump(mode="json")
    )
    db.add(calendar_event)
    db.commit()
    db.refresh(seek_request)

    matches = matching_service.find_matches(seek_request.id, db)
    logger.info(f"Created seek request {seek_request.id}, found {len(matches)} potential matches")

    return seek_request


@router.get("/seek", response_model=List[SeekRequestResponse])
async def list_seek_requests(
    req_status: Optional[RequestStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_seeker),
    db: Session = Depends(get_db)
):
    """List all seek requests for current user (auto-expires stale ones first)."""
    _auto_expire_requests(db)
    query = db.query(SeekRequest).filter(SeekRequest.seeker_id == current_user.id)
    if req_status:
        query = query.filter(SeekRequest.status == req_status)
    return query.order_by(SeekRequest.created_at.desc()).all()


@router.get("/seek/{request_id}", response_model=SeekRequestResponse)
async def get_seek_request(
    request_id: str,
    current_user: User = Depends(get_current_seeker),
    db: Session = Depends(get_db)
):
    """Get a specific seek request."""
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
    """Update a seek request.

    If the request is being cancelled, accepted volunteers are notified via
    email and their matches are marked as cancelled.
    Updating travel details or assistance also re-triggers matching.
    """
    seek_request = db.query(SeekRequest).filter(
        SeekRequest.id == request_id,
        SeekRequest.seeker_id == current_user.id
    ).first()

    if not seek_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seek request not found"
        )

    previously_active = seek_request.status == RequestStatus.ACTIVE

    if update_data.travel_details:
        seek_request.travel_details = update_data.travel_details.model_dump(mode="json")
    if update_data.assistance_needed:
        seek_request.assistance_needed = update_data.assistance_needed.model_dump(mode="json")
    if update_data.status:
        # Notify volunteer if request is being cancelled
        if update_data.status == RequestStatus.CANCELLED and previously_active:
            _notify_volunteers_on_seek_cancel(seek_request, db)
        seek_request.status = update_data.status

    db.commit()
    db.refresh(seek_request)

    # Re-trigger matching when travel details change and request is still active
    if previously_active and seek_request.status == RequestStatus.ACTIVE:
        matching_service.find_matches(seek_request.id, db)

    return seek_request


@router.delete("/seek/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seek_request(
    request_id: str,
    current_user: User = Depends(get_current_seeker),
    db: Session = Depends(get_db)
):
    """Cancel (soft-delete) a seek request.

    Instead of hard-deleting, the request is set to CANCELLED so that the
    history is preserved.  Accepted volunteers are notified via email.
    """
    seek_request = db.query(SeekRequest).filter(
        SeekRequest.id == request_id,
        SeekRequest.seeker_id == current_user.id
    ).first()

    if not seek_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seek request not found"
        )

    if seek_request.status == RequestStatus.ACTIVE:
        _notify_volunteers_on_seek_cancel(seek_request, db)

    seek_request.status = RequestStatus.CANCELLED
    db.commit()
    return None


# ---------------------------------------------------------------------------
# Volunteer Request Endpoints
# ---------------------------------------------------------------------------

@router.post("/volunteer", response_model=VolunteerRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_volunteer_request(
    request_data: VolunteerRequestCreate,
    current_user: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db)
):
    """Create a new volunteer request.

    A user may have at most VOLUNTEER_REQUEST_LIMIT active volunteer requests.
    Creating the request automatically triggers matching against all active
    seek requests so that seekers registered before this volunteer are not
    missed.
    """
    _auto_expire_requests(db)

    active_count = db.query(VolunteerRequest).filter(
        VolunteerRequest.volunteer_id == current_user.id,
        VolunteerRequest.status == RequestStatus.ACTIVE
    ).count()
    if active_count >= settings.VOLUNTEER_REQUEST_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"You have reached the maximum of {settings.VOLUNTEER_REQUEST_LIMIT} active volunteer requests."
        )

    travel_time = request_data.travel_details.travel_time
    expires_at = travel_time + timedelta(hours=24)

    volunteer_request = VolunteerRequest(
        volunteer_id=current_user.id,
        travel_details=request_data.travel_details.model_dump(mode="json"),
        assistance_offered=request_data.assistance_offered.model_dump(mode="json"),
        availability=request_data.availability.model_dump(mode="json") if request_data.availability else None,
        expires_at=expires_at
    )
    db.add(volunteer_request)
    db.flush()

    calendar_event = CalendarEvent(
        user_id=current_user.id,
        user_type=EventType.VOLUNTEER,
        request_id=volunteer_request.id,
        event_type=EventType.VOLUNTEER,
        title=f"Volunteer: {request_data.travel_details.source_airport} → {request_data.travel_details.destination_airport}",
        travel_details=request_data.travel_details.model_dump(mode="json")
    )
    db.add(calendar_event)
    db.commit()
    db.refresh(volunteer_request)

    # Trigger matching for existing seek requests
    matches = matching_service.find_matches_for_volunteer(volunteer_request.id, db)
    logger.info(f"Created volunteer request {volunteer_request.id}, found {len(matches)} potential matches")

    return volunteer_request


@router.get("/volunteer", response_model=List[VolunteerRequestResponse])
async def list_volunteer_requests(
    req_status: Optional[RequestStatus] = Query(None, alias="status"),
    current_user: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db)
):
    """List all volunteer requests for current user."""
    _auto_expire_requests(db)
    query = db.query(VolunteerRequest).filter(VolunteerRequest.volunteer_id == current_user.id)
    if req_status:
        query = query.filter(VolunteerRequest.status == req_status)
    return query.order_by(VolunteerRequest.created_at.desc()).all()


@router.get("/volunteer/{request_id}", response_model=VolunteerRequestResponse)
async def get_volunteer_request(
    request_id: str,
    current_user: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db)
):
    """Get a specific volunteer request."""
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
    """Update a volunteer request.

    Updating travel details or status re-triggers matching so that any newly
    compatible seek requests are discovered.
    """
    volunteer_request = db.query(VolunteerRequest).filter(
        VolunteerRequest.id == request_id,
        VolunteerRequest.volunteer_id == current_user.id
    ).first()

    if not volunteer_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer request not found"
        )

    previously_active = volunteer_request.status == RequestStatus.ACTIVE

    if update_data.travel_details:
        volunteer_request.travel_details = update_data.travel_details.model_dump(mode="json")
    if update_data.assistance_offered:
        volunteer_request.assistance_offered = update_data.assistance_offered.model_dump(mode="json")
    if update_data.availability:
        volunteer_request.availability = update_data.availability.model_dump(mode="json")
    if update_data.status:
        volunteer_request.status = update_data.status

    db.commit()
    db.refresh(volunteer_request)

    # Re-trigger matching when request is still active
    if previously_active and volunteer_request.status == RequestStatus.ACTIVE:
        matching_service.find_matches_for_volunteer(volunteer_request.id, db)

    return volunteer_request


@router.delete("/volunteer/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_volunteer_request(
    request_id: str,
    current_user: User = Depends(get_current_volunteer),
    db: Session = Depends(get_db)
):
    """Cancel a volunteer request (soft-delete)."""
    volunteer_request = db.query(VolunteerRequest).filter(
        VolunteerRequest.id == request_id,
        VolunteerRequest.volunteer_id == current_user.id
    ).first()

    if not volunteer_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer request not found"
        )

    volunteer_request.status = RequestStatus.CANCELLED
    db.commit()
    return None
