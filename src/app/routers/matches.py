from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User, UserType
from app.models.match import Match, MatchStatus
from app.models.request import SeekRequest, VolunteerRequest
from app.schemas.match import MatchResponse, MatchWithDetails
from app.services.matching_service import MatchingService
from app.utils.email import send_contact_exchange_notification
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
matching_service = MatchingService()


@router.get("/discover", response_model=List[MatchWithDetails])
async def discover_matches(
    request_id: Optional[str] = Query(None, description="Filter by specific request ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Discover matches for the current user.

    Returns matches for both the user's seek requests and their volunteer
    requests so that dual-role users see everything in one call.
    """
    result = []

    # --- Matches from seeker side ---
    seeker_query = db.query(Match).join(
        SeekRequest, Match.seek_request_id == SeekRequest.id
    ).filter(SeekRequest.seeker_id == current_user.id)

    if request_id:
        seeker_query = seeker_query.filter(Match.seek_request_id == request_id)

    for match in seeker_query.all():
        vol_request = db.query(VolunteerRequest).filter(
            VolunteerRequest.id == match.volunteer_request_id
        ).first()

        if vol_request:
            volunteer_user = db.query(User).filter(
                User.id == vol_request.volunteer_id
            ).first()

            result.append(MatchWithDetails(
                match_id=match.id,
                status=match.status,
                compatibility_score=match.match_score,
                request={
                    "request_id": vol_request.id,
                    "type": "volunteer",
                    "travel_details": vol_request.travel_details,
                    "assistance": vol_request.assistance_offered
                },
                user={
                    "name": volunteer_user.profile.get("name") if volunteer_user else None,
                    "languages_spoken": volunteer_user.profile.get("languages_spoken", []) if volunteer_user else []
                },
                created_at=match.created_at
            ))

    # --- Matches from volunteer side ---
    vol_query = db.query(Match).join(
        VolunteerRequest, Match.volunteer_request_id == VolunteerRequest.id
    ).filter(VolunteerRequest.volunteer_id == current_user.id)

    if request_id:
        vol_query = vol_query.filter(Match.volunteer_request_id == request_id)

    # Avoid duplicates when the user is matched with themselves (same user_id on both sides)
    existing_match_ids = {m.match_id for m in result}
    for match in vol_query.all():
        if match.id in existing_match_ids:
            continue

        seek_request = db.query(SeekRequest).filter(
            SeekRequest.id == match.seek_request_id
        ).first()

        if seek_request:
            seeker_user = db.query(User).filter(
                User.id == seek_request.seeker_id
            ).first()

            result.append(MatchWithDetails(
                match_id=match.id,
                status=match.status,
                compatibility_score=match.match_score,
                request={
                    "request_id": seek_request.id,
                    "type": "seek",
                    "travel_details": seek_request.travel_details,
                    "assistance": seek_request.assistance_needed
                },
                user={
                    "name": seeker_user.profile.get("name") if seeker_user else None,
                    "preferred_language": seeker_user.profile.get("preferred_language") if seeker_user else None
                },
                created_at=match.created_at
            ))

    return result


@router.post("/{match_id}/accept", response_model=MatchResponse)
async def accept_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record the volunteer's acceptance of a match."""

    match = db.query(Match).join(
        VolunteerRequest, Match.volunteer_request_id == VolunteerRequest.id
    ).filter(
        Match.id == match_id,
        VolunteerRequest.volunteer_id == current_user.id
    ).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found or you do not have a volunteer request linked to it"
        )

    if match.status != MatchStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending matches can be accepted by a volunteer"
        )

    match = matching_service.accept_match(match_id, db)

    logger.info(f"Match {match_id} accepted by volunteer {current_user.id}")
    return match


@router.post("/{match_id}/confirm", response_model=MatchResponse)
async def confirm_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Confirm a volunteer-accepted match as the seeker and exchange contacts."""
    match = db.query(Match).join(
        SeekRequest, Match.seek_request_id == SeekRequest.id
    ).filter(
        Match.id == match_id,
        SeekRequest.seeker_id == current_user.id
    ).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found or you do not have a seek request linked to it"
        )

    if match.status != MatchStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only matches accepted by the volunteer can be confirmed"
        )

    if match.communication and match.communication.get("contact_exchanged"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact details have already been exchanged"
        )

    volunteer_request = db.query(VolunteerRequest).filter(
        VolunteerRequest.id == match.volunteer_request_id
    ).first()
    volunteer = db.query(User).filter(
        User.id == volunteer_request.volunteer_id
    ).first() if volunteer_request else None
    if not volunteer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Volunteer associated with this match not found"
        )

    match = matching_service.confirm_match(match_id, db)

    send_contact_exchange_notification(
        to_email=current_user.email,
        contact_name=volunteer.profile.get("name"),
        contact_email=volunteer.email,
        contact_phone=volunteer.profile.get("phone")
    )

    send_contact_exchange_notification(
        to_email=volunteer.email,
        contact_name=current_user.profile.get("name"),
        contact_email=current_user.email,
        contact_phone=current_user.profile.get("phone")
    )

    logger.info(f"Match {match_id} confirmed by seeker {current_user.id}")
    return match


@router.post("/{match_id}/reject", response_model=MatchResponse)
async def reject_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a pending match as the volunteer or deny an accepted match as the seeker."""

    match = db.query(Match).filter(Match.id == match_id).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    volunteer_request = db.query(VolunteerRequest).filter(
        VolunteerRequest.id == match.volunteer_request_id,
        VolunteerRequest.volunteer_id == current_user.id
    ).first()
    seek_request = db.query(SeekRequest).filter(
        SeekRequest.id == match.seek_request_id,
        SeekRequest.seeker_id == current_user.id
    ).first()
    may_reject_as_volunteer = (
        volunteer_request is not None and match.status == MatchStatus.PENDING
    )
    may_deny_as_seeker = (
        seek_request is not None
        and match.status == MatchStatus.ACCEPTED
        and not (match.communication and match.communication.get("contact_exchanged"))
    )
    if not may_reject_as_volunteer and not may_deny_as_seeker:
        if not volunteer_request and not seek_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found or you are not a participant"
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Match cannot be rejected in its current state"
        )

    match = matching_service.reject_match(match_id, db)
    logger.info(f"Match {match_id} rejected by user {current_user.id}")
    return match


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific match (user must be a seeker or volunteer party)."""

    match = db.query(Match).filter(Match.id == match_id).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    # Check seeker access
    seek_request = db.query(SeekRequest).filter(
        SeekRequest.id == match.seek_request_id,
        SeekRequest.seeker_id == current_user.id
    ).first()

    # Check volunteer access
    vol_request = db.query(VolunteerRequest).filter(
        VolunteerRequest.id == match.volunteer_request_id,
        VolunteerRequest.volunteer_id == current_user.id
    ).first()

    if not seek_request and not vol_request:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return match
