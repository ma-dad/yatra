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
    Discover matches for the current user
    - For seekers: shows volunteers who can help with their requests
    - For volunteers: shows seekers who need help on their routes
    """
    
    if current_user.user_type == UserType.SEEKER:
        # Get matches for seeker's requests
        query = db.query(Match).join(
            SeekRequest, Match.seek_request_id == SeekRequest.id
        ).filter(SeekRequest.seeker_id == current_user.id)
        
        if request_id:
            query = query.filter(Match.seek_request_id == request_id)
        
        matches = query.all()
        
        # Format response with volunteer details
        result = []
        for match in matches:
            vol_request = db.query(VolunteerRequest).filter(
                VolunteerRequest.id == match.volunteer_request_id
            ).first()
            
            if vol_request:
                volunteer_user = db.query(User).filter(
                    User.id == vol_request.volunteer_id
                ).first()
                
                result.append(MatchWithDetails(
                    match_id=match.id,
                    compatibility_score=match.match_score,
                    request={
                        "request_id": vol_request.id,
                        "type": "volunteer",
                        "travel_details": vol_request.travel_details,
                        "assistance": vol_request.assistance_offered
                    },
                    user={
                        "name": volunteer_user.profile.get("name"),
                        "languages_spoken": volunteer_user.profile.get("languages_spoken", [])
                    },
                    created_at=match.created_at
                ))
    
    else:  # Volunteer
        # Get matches for volunteer's requests
        query = db.query(Match).join(
            VolunteerRequest, Match.volunteer_request_id == VolunteerRequest.id
        ).filter(VolunteerRequest.volunteer_id == current_user.id)
        
        if request_id:
            query = query.filter(Match.volunteer_request_id == request_id)
        
        matches = query.all()
        
        # Format response with seeker details
        result = []
        for match in matches:
            seek_request = db.query(SeekRequest).filter(
                SeekRequest.id == match.seek_request_id
            ).first()
            
            if seek_request:
                seeker_user = db.query(User).filter(
                    User.id == seek_request.seeker_id
                ).first()
                
                result.append(MatchWithDetails(
                    match_id=match.id,
                    compatibility_score=match.match_score,
                    request={
                        "request_id": seek_request.id,
                        "type": "seek",
                        "travel_details": seek_request.travel_details,
                        "assistance": seek_request.assistance_needed
                    },
                    user={
                        "name": seeker_user.profile.get("name"),
                        "preferred_language": seeker_user.profile.get("preferred_language")
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
    """Accept a match (volunteers only)"""
    
    if current_user.user_type != UserType.VOLUNTEER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only volunteers can accept matches"
        )
    
    # Verify match belongs to volunteer
    match = db.query(Match).join(
        VolunteerRequest, Match.volunteer_request_id == VolunteerRequest.id
    ).filter(
        Match.id == match_id,
        VolunteerRequest.volunteer_id == current_user.id
    ).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    # Accept the match
    match = matching_service.accept_match(match_id, db)
    
    # Get seeker details for notification
    seek_request = db.query(SeekRequest).filter(
        SeekRequest.id == match.seek_request_id
    ).first()
    seeker = db.query(User).filter(User.id == seek_request.seeker_id).first()
    
    # Send contact exchange notification
    send_contact_exchange_notification(
        to_email=seeker.email,
        contact_name=current_user.profile.get("name"),
        contact_email=current_user.email,
        contact_phone=current_user.profile.get("phone")
    )
    
    send_contact_exchange_notification(
        to_email=current_user.email,
        contact_name=seeker.profile.get("name"),
        contact_email=seeker.email,
        contact_phone=seeker.profile.get("phone")
    )
    
    logger.info(f"Match {match_id} accepted by volunteer {current_user.id}")
    
    return match


@router.post("/{match_id}/reject", response_model=MatchResponse)
async def reject_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a match (volunteers only)"""
    
    if current_user.user_type != UserType.VOLUNTEER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only volunteers can reject matches"
        )
    
    # Verify match belongs to volunteer
    match = db.query(Match).join(
        VolunteerRequest, Match.volunteer_request_id == VolunteerRequest.id
    ).filter(
        Match.id == match_id,
        VolunteerRequest.volunteer_id == current_user.id
    ).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    # Reject the match
    match = matching_service.reject_match(match_id, db)
    
    logger.info(f"Match {match_id} rejected by volunteer {current_user.id}")
    
    return match


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific match"""
    
    match = db.query(Match).filter(Match.id == match_id).first()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    # Verify user has access to this match
    if current_user.user_type == UserType.SEEKER:
        seek_request = db.query(SeekRequest).filter(
            SeekRequest.id == match.seek_request_id,
            SeekRequest.seeker_id == current_user.id
        ).first()
        if not seek_request:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    else:
        volunteer_request = db.query(VolunteerRequest).filter(
            VolunteerRequest.id == match.volunteer_request_id,
            VolunteerRequest.volunteer_id == current_user.id
        ).first()
        if not volunteer_request:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return match
