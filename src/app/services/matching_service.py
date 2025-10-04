from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.request import SeekRequest, VolunteerRequest, RequestStatus
from app.models.match import Match, MatchStatus
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for matching seekers with volunteers"""
    
    def calculate_compatibility_score(
        self, 
        seek_request: SeekRequest, 
        volunteer_request: VolunteerRequest
    ) -> float:
        """Calculate compatibility score between a seek and volunteer request"""
        
        score = 0.0
        seek_travel = seek_request.travel_details
        vol_travel = volunteer_request.travel_details
        
        # Route match (40 points)
        if (seek_travel.get('source_airport') == vol_travel.get('source_airport') and
            seek_travel.get('destination_airport') == vol_travel.get('destination_airport')):
            score += 40
        
        # Flight number match (30 points) - highest priority if same flight
        if seek_travel.get('flight_number') == vol_travel.get('flight_number'):
            score += 30
        else:
            # Time proximity (30 points if no flight match)
            seek_time = datetime.fromisoformat(seek_travel.get('travel_time', ''))
            vol_time = datetime.fromisoformat(vol_travel.get('travel_time', ''))
            time_diff = abs((seek_time - vol_time).total_seconds() / 3600)  # hours
            
            if time_diff <= 4:  # Within 4 hours
                score += 30 * (1 - time_diff / 4)
        
        # Language match (20 points) - check if volunteer speaks seeker's language
        # Note: This would need user profile data, simplified for now
        score += 10  # Basic language compatibility assumption
        
        # Category match (10 points) - check if assistance types align
        seek_categories = set(seek_request.assistance_needed.get('categories', []))
        vol_categories = set(volunteer_request.assistance_offered.get('categories', []))
        if seek_categories & vol_categories:  # Any intersection
            score += 10
        
        return min(score, 100.0)  # Cap at 100
    
    def find_matches(
        self, 
        seek_request_id: str, 
        db: Session,
        min_score: float = 50.0
    ) -> List[Match]:
        """Find compatible volunteer requests for a seek request"""
        
        seek_request = db.query(SeekRequest).filter(
            SeekRequest.id == seek_request_id,
            SeekRequest.status == RequestStatus.ACTIVE
        ).first()
        
        if not seek_request:
            return []
        
        # Find active volunteer requests
        volunteer_requests = db.query(VolunteerRequest).filter(
            VolunteerRequest.status == RequestStatus.ACTIVE
        ).all()
        
        matches = []
        for vol_request in volunteer_requests:
            score = self.calculate_compatibility_score(seek_request, vol_request)
            
            if score >= min_score:
                # Check if match already exists
                existing_match = db.query(Match).filter(
                    Match.seek_request_id == seek_request_id,
                    Match.volunteer_request_id == vol_request.id
                ).first()
                
                if not existing_match:
                    match = Match(
                        seek_request_id=seek_request_id,
                        volunteer_request_id=vol_request.id,
                        match_score=score,
                        status=MatchStatus.PENDING
                    )
                    db.add(match)
                    matches.append(match)
        
        db.commit()
        logger.info(f"Found {len(matches)} matches for seek request {seek_request_id}")
        return matches
    
    def accept_match(
        self, 
        match_id: str, 
        db: Session
    ) -> Optional[Match]:
        """Accept a match"""
        
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            return None
        
        match.status = MatchStatus.ACCEPTED
        match.communication = {
            "contact_exchanged": True,
            "last_message_at": datetime.utcnow().isoformat()
        }
        
        db.commit()
        db.refresh(match)
        
        logger.info(f"Match {match_id} accepted")
        return match
    
    def reject_match(
        self, 
        match_id: str, 
        db: Session
    ) -> Optional[Match]:
        """Reject a match"""
        
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            return None
        
        match.status = MatchStatus.REJECTED
        db.commit()
        db.refresh(match)
        
        logger.info(f"Match {match_id} rejected")
        return match
