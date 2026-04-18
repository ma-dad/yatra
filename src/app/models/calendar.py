from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, JSON, ForeignKey, inspect, text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


def upgrade_calendar_event_is_public_column(engine):
    """
    Upgrade legacy calendar_events.is_public columns that were created as strings.

    Base.metadata.create_all() does not alter existing columns, so deployments that
    created this column before it was changed to Boolean need an explicit upgrade.
    This helper is idempotent and safely converts legacy string values such as
    "true"/"false" to booleans before changing the schema.
    """
    inspector = inspect(engine)

    if "calendar_events" not in inspector.get_table_names():
        return

    columns = {column["name"]: column for column in inspector.get_columns("calendar_events")}
    is_public_column = columns.get("is_public")
    if is_public_column is None:
        return

    column_type = str(is_public_column["type"]).lower()
    if "bool" in column_type:
        return

    with engine.begin() as connection:
        dialect = connection.dialect.name

        if dialect == "postgresql":
            connection.execute(text("""
                ALTER TABLE calendar_events
                ALTER COLUMN is_public TYPE BOOLEAN
                USING CASE
                    WHEN lower(trim(coalesce(is_public::text, 'true'))) IN ('true', '1', 't', 'yes', 'y', 'on')
                        THEN TRUE
                    ELSE FALSE
                END
            """))
            connection.execute(text("""
                ALTER TABLE calendar_events
                ALTER COLUMN is_public SET DEFAULT TRUE
            """))
        elif dialect == "mysql":
            connection.execute(text("""
                UPDATE calendar_events
                SET is_public = CASE
                    WHEN lower(trim(coalesce(CAST(is_public AS CHAR), 'true'))) IN ('true', '1', 't', 'yes', 'y', 'on')
                        THEN '1'
                    ELSE '0'
                END
            """))
            connection.execute(text("""
                ALTER TABLE calendar_events
                MODIFY COLUMN is_public BOOLEAN DEFAULT TRUE
            """))
        elif dialect == "sqlite":
            connection.execute(text("""
                ALTER TABLE calendar_events
                RENAME TO calendar_events__legacy
            """))
            connection.execute(text("""
                CREATE TABLE calendar_events (
                    id VARCHAR NOT NULL,
                    user_id VARCHAR NOT NULL,
                    user_type VARCHAR(9) NOT NULL,
                    request_id VARCHAR NOT NULL,
                    event_type VARCHAR(9) NOT NULL,
                    title VARCHAR NOT NULL,
                    travel_details JSON NOT NULL,
                    is_public BOOLEAN,
                    created_at DATETIME,
                    updated_at DATETIME,
                    PRIMARY KEY (id)
                )
            """))
            connection.execute(text("""
                INSERT INTO calendar_events (
                    id,
                    user_id,
                    user_type,
                    request_id,
                    event_type,
                    title,
                    travel_details,
                    is_public,
                    created_at,
                    updated_at
                )
                SELECT
                    id,
                    user_id,
                    user_type,
                    request_id,
                    event_type,
                    title,
                    travel_details,
                    CASE
                        WHEN lower(trim(coalesce(CAST(is_public AS TEXT), 'true'))) IN ('true', '1', 't', 'yes', 'y', 'on')
                            THEN 1
                        ELSE 0
                    END,
                    created_at,
                    updated_at
                FROM calendar_events__legacy
            """))
            connection.execute(text("""
                DROP TABLE calendar_events__legacy
            """))
        else:
            raise RuntimeError(
                f"Unsupported database dialect for calendar_events.is_public migration: {dialect}"
            )


class EventType(str, enum.Enum):
    SEEK = "seek"
    VOLUNTEER = "volunteer"


class CalendarEvent(Base):
    """Model for calendar events representing travel plans"""
    __tablename__ = "calendar_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    user_type = Column(SQLEnum(EventType), nullable=False)
    request_id = Column(String, nullable=False)
    event_type = Column(SQLEnum(EventType), nullable=False)
    
    title = Column(String, nullable=False)
    
    # Travel details stored as JSON
    travel_details = Column(JSON, nullable=False)
    
    # Event visibility and metadata
    # Existing deployments with a legacy string column must run
    # upgrade_calendar_event_is_public_column(engine) before relying on this Boolean type.
    is_public = Column(Boolean, default=True)  # For future privacy controls
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - Note: These use string-based foreign keys for flexibility
    seeker = relationship("Seeker", 
                         foreign_keys=[user_id],
                         primaryjoin="and_(CalendarEvent.user_id==Seeker.user_id, CalendarEvent.user_type=='seek')",
                         back_populates="calendar_events", viewonly=True)
    
    volunteer = relationship("Volunteer",
                            foreign_keys=[user_id],
                            primaryjoin="and_(CalendarEvent.user_id==Volunteer.user_id, CalendarEvent.user_type=='volunteer')",
                            back_populates="calendar_events", viewonly=True)
    
    seek_request = relationship("SeekRequest",
                               foreign_keys=[request_id],
                               primaryjoin="and_(CalendarEvent.request_id==SeekRequest.id, CalendarEvent.event_type=='seek')",
                               back_populates="calendar_events", viewonly=True)
    
    volunteer_request = relationship("VolunteerRequest",
                                    foreign_keys=[request_id],
                                    primaryjoin="and_(CalendarEvent.request_id==VolunteerRequest.id, CalendarEvent.event_type=='volunteer')",
                                    back_populates="calendar_events", viewonly=True)
