from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.calendar import CalendarEvent
from app.schemas.calendar import CalendarEventResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[CalendarEventResponse])
async def get_calendar_events(
    start_date: Optional[str] = Query(None, description="Start date in ISO format"),
    end_date: Optional[str] = Query(None, description="End date in ISO format"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get calendar events for the current user within a date range
    Shows user's own travel plans and potential matches
    """
    
    query = db.query(CalendarEvent).filter(CalendarEvent.user_id == current_user.id)
    
    # Filter by date range if provided
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            # Filter events where travel_time >= start_date
            events = query.all()
            events = [e for e in events if datetime.fromisoformat(
                e.travel_details.get('travel_time', '')) >= start_dt]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format."
            )
    else:
        events = query.all()
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            # Filter events where travel_time <= end_date
            events = [e for e in events if datetime.fromisoformat(
                e.travel_details.get('travel_time', '')) <= end_dt]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format."
            )
    
    # Sort by travel time
    events.sort(key=lambda e: e.travel_details.get('travel_time', ''))
    
    return events


@router.get("/public", response_model=List[CalendarEventResponse])
async def get_public_calendar_events(
    start_date: Optional[str] = Query(None, description="Start date in ISO format"),
    end_date: Optional[str] = Query(None, description="End date in ISO format"),
    airport: Optional[str] = Query(None, description="Filter by airport (source or destination)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get public calendar events from all users
    Useful for seekers to find volunteers and vice versa
    """
    
    query = db.query(CalendarEvent).filter(CalendarEvent.is_public == "true")
    
    # Exclude current user's events
    query = query.filter(CalendarEvent.user_id != current_user.id)
    
    events = query.all()
    
    # Filter by date range if provided
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            events = [e for e in events if datetime.fromisoformat(
                e.travel_details.get('travel_time', '')) >= start_dt]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format."
            )
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            events = [e for e in events if datetime.fromisoformat(
                e.travel_details.get('travel_time', '')) <= end_dt]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format."
            )
    
    # Filter by airport if provided
    if airport:
        events = [e for e in events if (
            e.travel_details.get('source_airport') == airport or
            e.travel_details.get('destination_airport') == airport
        )]
    
    # Sort by travel time
    events.sort(key=lambda e: e.travel_details.get('travel_time', ''))
    
    return events
