from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.request import SeekRequest, VolunteerRequest, RequestStatus
from app.models.match import Match, MatchStatus
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class MatchingService:
    """Service for matching seekers with volunteers.

    Matching logic (simple, non-point-based):
    A seek request and a volunteer request are considered a match when:
      1. They share the same source AND destination airport (same trajectory), AND
      2. Either:
         a. They have the same flight number, OR
         b. Their departure times are within MATCH_TIME_BUFFER_HOURS of each other.

    The buffer is read from ``settings.MATCH_TIME_BUFFER_HOURS`` so it can be
    tuned via environment variable without code changes.
    """

    # ------------------------------------------------------------------
    # Core matching predicate
    # ------------------------------------------------------------------

    def is_match(
        self,
        seek_request: SeekRequest,
        volunteer_request: VolunteerRequest,
    ) -> bool:
        """Return True if the two requests are a match."""
        seek_travel = seek_request.travel_details
        vol_travel = volunteer_request.travel_details

        # Condition 1: same trajectory (source + destination)
        same_route = (
            seek_travel.get('source_airport') == vol_travel.get('source_airport')
            and seek_travel.get('destination_airport') == vol_travel.get('destination_airport')
        )
        if not same_route:
            return False

        # Condition 2a: same flight number
        seek_flight = seek_travel.get('flight_number', '')
        vol_flight = vol_travel.get('flight_number', '')
        if seek_flight and vol_flight and seek_flight == vol_flight:
            return True

        # Condition 2b: departure times within the configured buffer
        try:
            seek_time = datetime.fromisoformat(seek_travel.get('travel_time', ''))
            vol_time = datetime.fromisoformat(vol_travel.get('travel_time', ''))
            hours_diff = abs((seek_time - vol_time).total_seconds() / 3600)
            if hours_diff <= settings.MATCH_TIME_BUFFER_HOURS:
                return True
        except (ValueError, TypeError):
            pass

        return False

    # ------------------------------------------------------------------
    # Match discovery helpers
    # ------------------------------------------------------------------

    def find_matches(
        self,
        seek_request_id: str,
        db: Session,
    ) -> List[Match]:
        """Find compatible volunteer requests for a seek request and persist
        new Match records.  Called whenever a seek request is created or
        updated.
        """
        seek_request = db.query(SeekRequest).filter(
            SeekRequest.id == seek_request_id,
            SeekRequest.status == RequestStatus.ACTIVE
        ).first()

        if not seek_request:
            return []

        volunteer_requests = db.query(VolunteerRequest).filter(
            VolunteerRequest.status == RequestStatus.ACTIVE
        ).all()

        new_matches: List[Match] = []
        for vol_request in volunteer_requests:
            if not self.is_match(seek_request, vol_request):
                continue

            existing = db.query(Match).filter(
                Match.seek_request_id == seek_request_id,
                Match.volunteer_request_id == vol_request.id
            ).first()

            if not existing:
                match = Match(
                    seek_request_id=seek_request_id,
                    volunteer_request_id=vol_request.id,
                    match_score=1.0,  # Boolean match indicator; 1.0 = match found
                    status=MatchStatus.PENDING
                )
                db.add(match)
                new_matches.append(match)

        db.commit()
        logger.info(
            "Found %d new matches for seek request %s",
            len(new_matches),
            seek_request_id,
        )
        return new_matches

    def find_matches_for_volunteer(
        self,
        volunteer_request_id: str,
        db: Session,
    ) -> List[Match]:
        """Find compatible seek requests for a volunteer request and persist new
        Match records.  Called whenever a volunteer request is created or
        updated so that existing seekers are not missed.
        """
        vol_request = db.query(VolunteerRequest).filter(
            VolunteerRequest.id == volunteer_request_id,
            VolunteerRequest.status == RequestStatus.ACTIVE
        ).first()

        if not vol_request:
            return []

        seek_requests = db.query(SeekRequest).filter(
            SeekRequest.status == RequestStatus.ACTIVE
        ).all()

        new_matches: List[Match] = []
        for seek_request in seek_requests:
            if not self.is_match(seek_request, vol_request):
                continue

            existing = db.query(Match).filter(
                Match.seek_request_id == seek_request.id,
                Match.volunteer_request_id == volunteer_request_id
            ).first()

            if not existing:
                match = Match(
                    seek_request_id=seek_request.id,
                    volunteer_request_id=volunteer_request_id,
                    match_score=1.0,  # Boolean match indicator; 1.0 = match found
                    status=MatchStatus.PENDING
                )
                db.add(match)
                new_matches.append(match)

        db.commit()
        logger.info(
            "Found %d new matches for volunteer request %s",
            len(new_matches),
            volunteer_request_id,
        )
        return new_matches

    # ------------------------------------------------------------------
    # Match state transitions
    # ------------------------------------------------------------------

    def accept_match(self, match_id: str, db: Session) -> Optional[Match]:
        """Accept a match"""
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            return None

        match.status = MatchStatus.ACCEPTED
        match.communication = {
            "contact_exchanged": True,
            "last_message_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        }
        db.commit()
        db.refresh(match)
        logger.info(f"Match {match_id} accepted")
        return match

    def reject_match(self, match_id: str, db: Session) -> Optional[Match]:
        """Reject a match"""
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            return None

        match.status = MatchStatus.REJECTED
        db.commit()
        db.refresh(match)
        logger.info(f"Match {match_id} rejected")
        return match
