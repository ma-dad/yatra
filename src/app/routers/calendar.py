from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.calendar import CalendarEvent
from app.schemas.calendar import CalendarEventResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

_DATETIME_MIN = datetime.min.replace(tzinfo=timezone.utc)


def _to_utc(dt: datetime) -> datetime:
    """Convert *dt* to UTC.  Naive datetimes are assumed to be UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _event_travel_time(event: CalendarEvent) -> datetime:
    """Return the travel_time as a UTC-aware datetime for *event*, or ``_DATETIME_MIN`` on parse failure.

    Naive datetimes stored in travel_details are assumed to be UTC.
    Tz-aware datetimes are converted to UTC so that comparisons across different
    offsets (or mixed naive/aware values) are always correct.
    """
    try:
        return _to_utc(datetime.fromisoformat(event.travel_details.get('travel_time', '')))
    except (ValueError, TypeError):
        return _DATETIME_MIN


def _filter_events_by_date(
    events: list,
    start_date: Optional[str],
    end_date: Optional[str],
) -> list:
    """Filter *events* to those whose travel_time falls within [start_date, end_date].

    Raises HTTPException 400 if either date string is not valid ISO format.
    All datetimes are normalised to UTC before comparison: tz-aware values are
    converted to UTC; naive values are assumed to be UTC.  Events whose
    travel_time cannot be parsed are excluded when a date filter is active.
    """
    if start_date:
        try:
            start_dt = _to_utc(datetime.fromisoformat(start_date))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format."
            )
        events = [e for e in events if (et := _event_travel_time(e)) != _DATETIME_MIN and et >= start_dt]

    if end_date:
        try:
            end_dt = _to_utc(datetime.fromisoformat(end_date))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format."
            )
        events = [e for e in events if (et := _event_travel_time(e)) != _DATETIME_MIN and et <= end_dt]

    return events


@router.get("/", response_model=List[CalendarEventResponse])
async def get_calendar_events(
    start_date: Optional[str] = Query(None, description="Start date in ISO format"),
    end_date: Optional[str] = Query(None, description="End date in ISO format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get calendar events for the current authenticated user within a date range.
    Shows user's own travel plans and potential matches.
    """

    query = db.query(CalendarEvent).filter(CalendarEvent.user_id == current_user.id)
    events = query.all()

    events = _filter_events_by_date(events, start_date, end_date)
    events.sort(key=_event_travel_time)
    return events


@router.get("/all", response_model=List[CalendarEventResponse])
async def get_all_calendar_events(
    start_date: Optional[str] = Query(None, description="Start date in ISO format"),
    end_date: Optional[str] = Query(None, description="End date in ISO format"),
    airport: Optional[str] = Query(None, description="Filter by airport (source or destination)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get calendar events from all users (requires authentication).

    The calendar is not publicly accessible — only authenticated users may
    browse other users' travel plans to discover potential matches.
    """

    # Exclude the current user's own events (they can see those via GET /)
    query = db.query(CalendarEvent).filter(CalendarEvent.user_id != current_user.id)
    events = query.all()

    events = _filter_events_by_date(events, start_date, end_date)

    if airport:
        events = [e for e in events if (
            e.travel_details.get('source_airport') == airport or
            e.travel_details.get('destination_airport') == airport
        )]

    events.sort(key=_event_travel_time)
    return events
