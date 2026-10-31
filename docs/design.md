# Yatra Platform - System Design & API Specification

## Overview
This document defines the complete system design for the Yatra community travel assistance platform, including data structures, user operations, and API specifications for connecting travelers who need help with volunteers who can assist them.

## Related docs

- [Project README](PROJECT.md)
- [Quick Start](QUICKSTART.md)
- [Implementation Guide](implementation.md)
- [Phase 1 Summary](PHASE1_SUMMARY.md)
- [Upgrading](UPGRADING.md)
- [Source Guide](../src/README.md)

---

## Data Models

### 1. User Types

#### Seeker
A user who needs assistance during travel.

**Entity Relationship Diagram:**
```
┌─────────────────────────────────────────────────────────────┐
│                        SEEKER                               │
├─────────────────────────────────────────────────────────────┤
│ + id: UUID (PK)                                             │
│ + google_id: string (Unique)                                │
│ + email: string (Unique)                                    │
│ + created_at: datetime                                      │
│ + updated_at: datetime                                      │
│                                                             │
│ ┌─────────────── PROFILE ───────────────┐                   │
│ │ + name: string                        │                   │
│ │ + google_picture: string (optional)   │                   │
│ │ + phone: string (optional)            │                   │
│ │ + preferred_language: string          │                   │
│ │                                       │                   │
│ │ ┌───── EMERGENCY_CONTACT ─────┐       │                   │
│ │ │ + name: string              │       │                   │
│ │ │ + phone: string             │       │                   │
│ │ │ + email: string             │       │                   │
│ │ └─────────────────────────────┘       │                   │
│ └───────────────────────────────────────┘                   │
│                                                             │
│ ┌─────────────── AUTH ──────────────────┐                   │
│ │ + refresh_token: string (encrypted)   │                   │
│ │ + last_login: datetime                │                   │
│ └───────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│   SEEK_REQUEST  │
└─────────────────┘
```

**Database Schema:**
```json
{
  "id": "string (UUID)",
  "google_id": "string (Google user ID)",
  "email": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "profile": {
    "name": "string",
    "google_picture": "string (URL Optional)",
    "phone": "string (optional)",
    "preferred_language": "string",
    "emergency_contact": {
      "name": "string",
      "phone": "string",
      "email": "string"
    }
  },
  "auth": {
    "refresh_token": "string (encrypted)",
    "last_login": "datetime"
  }
}
```

#### Volunteer
A user who offers assistance to other travelers during their own journeys.

**Entity Relationship Diagram:**
```
┌──────────────────────────────────────────────────────────────────────┐
│                           VOLUNTEER                                  │
├──────────────────────────────────────────────────────────────────────┤
│ + id: UUID (PK)                                                      │
│ + google_id: string (Unique)                                         │
│ + email: string (Unique)                                             │
│ + created_at: datetime                                               │
│ + updated_at: datetime                                               │
│                                                                      │
│ ┌─────────────── PROFILE ───────────────────┐                        │
│ │ + name: string                            │                        │
│ │ + google_picture: string (optional)       │                        │
│ │ + phone: string (optional)                │                        │
│ │ + preferred_language: string              │                        │
│ │ + languages_spoken: array[string]         │                        │
│ │ + experience_level: enum                  │                        │
│ │ + specialties: array[string]              │                        │
│ └───────────────────────────────────────────┘                        │
│                                                                      │
│ ┌─────────────── AUTH ──────────────────────┐                        │
│ │ + refresh_token: string (encrypted)       │                        │
│ │ + last_login: datetime                    │                        │
│ └───────────────────────────────────────────┘                        │
└──────────────────────────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────────┐
│ VOLUNTEER_REQUEST   │
└─────────────────────┘
```

**Database Schema:**
```json
{
  "id": "string (UUID)",
  "google_id": "string (Google user ID)",
  "email": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "profile": {
    "name": "string",
    "google_picture": "string (URL Optional)",
    "phone": "string (optional)",
    "preferred_language": "string",
    "languages_spoken": ["string"],
    "experience_level": "string (beginner|intermediate|expert)",
    "specialties": ["string"] // e.g., ["elderly_assistance", "immigration_help", "language_translation"]
  },
  "auth": {
    "refresh_token": "string (encrypted)",
    "last_login": "datetime"
  }
}
```

### 2. Request Types

#### Seek Request
A request for assistance created by a seeker.

**Entity Relationship Diagram:**
```
┌─────────────────────────────────────────────────────────────────────┐
│                          SEEK_REQUEST                              │
├─────────────────────────────────────────────────────────────────────┤
│ + id: UUID (PK)                                                     │
│ + seeker_id: UUID (FK → SEEKER)                                    │
│ + type: "seek"                                                      │
│ + status: enum (active|matched|completed|cancelled)                │
│ + created_at: datetime                                              │
│ + updated_at: datetime                                              │
│ + expires_at: datetime                                              │
│                                                                     │
│ ┌─────────────── TRAVEL_DETAILS ──────────────┐                     │
│ │ + travel_time: datetime                     │                     │
│ │ + source_airport: string (IATA)             │                     │
│ │ + destination_airport: string (IATA)        │                     │
│ │ + airline: string                           │                     │
│ │ + flight_number: string                     │                     │
│ │ + number_of_people: integer                 │                     │
│ │                                             │                     │
│ │ ┌───── LAYOVER ─────┐                       │                     │
│ │ │ + has_layover: bool│                       │                     │
│ │ │ + airport: string │                       │                     │
│ │ │ + duration: int   │                       │                     │
│ │ └───────────────────┘                       │                     │
│ └─────────────────────────────────────────────┘                     │
│                                                                     │
│ ┌─────────────── ASSISTANCE_NEEDED ───────────┐                     │
│ │ + type: "travel_companion"                  │                     │
│ │ + categories: array[string]                 │                     │
│ │ + special_requirements: array[string]       │                     │
│ │ + comments: string                          │                     │
│ └─────────────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│     MATCH       │
└─────────────────┘
```

**Database Schema:**
```json
{
  "id": "string (UUID)",
  "seeker_id": "string (UUID)",
  "type": "seek",
  "status": "string (active|matched|completed|cancelled)",
  "travel_details": {
    "travel_time": "datetime",
    "source_airport": "string (IATA code)",
    "destination_airport": "string (IATA code)",
    "airline": "string",
    "flight_number": "string",
    "number_of_people": "integer",
    "layover": {
      "has_layover": "boolean",
      "layover_airport": "string (IATA code, optional)",
      "layover_duration": "integer (minutes, optional)"
    }
  },
  "assistance_needed": {
    "type": "string (travel_companion)",
    "categories": ["string"], // e.g., ["immigration_help", "navigation", "language_assistance"]
    "special_requirements": ["string"], // e.g., ["wheelchair_assistance", "medical_needs"]
    "comments": "string"
  },
  "created_at": "datetime",
  "updated_at": "datetime",
  "expires_at": "datetime"
}
```

#### Volunteer Request
An offer of assistance created by a volunteer.

**Entity Relationship Diagram:**
```
┌──────────────────────────────────────────────────────────────────────┐
│                       VOLUNTEER_REQUEST                             │
├──────────────────────────────────────────────────────────────────────┤
│ + id: UUID (PK)                                                      │
│ + volunteer_id: UUID (FK → VOLUNTEER)                               │
│ + type: "volunteer"                                                  │
│ + status: enum (available|matched|completed|expired)                │
│ + created_at: datetime                                               │
│ + updated_at: datetime                                               │
│ + expires_at: datetime                                               │
│                                                                      │
│ ┌─────────────── TRAVEL_DETAILS ──────────────┐                      │
│ │ + travel_time: datetime                     │                      │
│ │ + source_airport: string (IATA)             │                      │
│ │ + destination_airport: string (IATA)        │                      │
│ │ + airline: string                           │                      │
│ │ + flight_number: string                     │                      │
│ │ + number_of_people: integer                 │                      │
│ │                                             │                      │
│ │ ┌───── LAYOVER ─────┐                       │                      │
│ │ │ + has_layover: bool│                       │                      │
│ │ │ + airport: string │                       │                      │
│ │ │ + duration: int   │                       │                      │
│ │ └───────────────────┘                       │                      │
│ └─────────────────────────────────────────────┘                      │
│                                                                      │
│ ┌─────────────── ASSISTANCE_OFFERED ──────────┐                      │
│ │ + types: array[string]                      │                      │
│ │ + categories: array[string]                 │                      │
│ │ + comments: string                          │                      │
│ └─────────────────────────────────────────────┘                      │
│                                                                      │
│ ┌─────────────── AVAILABILITY ────────────────┐                      │
│ │ + flexible_timing: boolean                  │                      │
│ │ + time_buffer: integer (hours)              │                      │
│ └─────────────────────────────────────────────┘                      │
└──────────────────────────────────────────────────────────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│     MATCH       │
└─────────────────┘
```

**Database Schema:**
```json
{
  "id": "string (UUID)",
  "volunteer_id": "string (UUID)",
  "type": "volunteer",
  "status": "string (available|matched|completed|expired)",
  "travel_details": {
    "travel_time": "datetime",
    "source_airport": "string (IATA code)",
    "destination_airport": "string (IATA code)",
    "airline": "string",
    "flight_number": "string",
    "number_of_people": "integer",
    "layover": {
      "has_layover": "boolean",
      "layover_airport": "string (IATA code, optional)",
      "layover_duration": "integer (minutes, optional)"
    }
  },
  "assistance_offered": {
    "types": ["string"], // e.g., ["travel_companion"]
    "categories": ["string"], // e.g., ["immigration_help", "navigation", "language_assistance"]
    "comments": "string"
  },
  "availability": {
    "flexible_timing": "boolean",
    "time_buffer": "integer (hours)" // how much flexibility in timing
  },
  "created_at": "datetime",
  "updated_at": "datetime",
  "expires_at": "datetime"
}
```

### 3. Match & Interaction Models

#### Match
Represents a connection between a seek request and volunteer request.

**Entity Relationship Diagram:**
```
┌─────────────────────────────────────────────────────────────────────┐
│                            MATCH                                   │
├─────────────────────────────────────────────────────────────────────┤
│ + id: UUID (PK)                                                     │
│ + seek_request_id: UUID (FK → SEEK_REQUEST)                        │
│ + volunteer_request_id: UUID (FK → VOLUNTEER_REQUEST)              │
│ + status: enum (pending|accepted|rejected|completed|cancelled)     │
│ + match_score: float                                                │
│ + created_at: datetime                                              │
│ + updated_at: datetime                                              │
│                                                                     │
│ ┌─────────────── COMMUNICATION ───────────────┐                     │
│ │ + contact_exchanged: boolean                │                     │
│ │ + last_message_at: datetime                 │                     │
│ └─────────────────────────────────────────────┘                     │
│                                                                     │
│ ┌─────────────── COMPLETION ──────────────────┐                     │
│ │ + completed_at: datetime                    │                     │
│ └─────────────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  SEEK_REQUEST   │ ──1:N─ │      MATCH      │ ─N:1─ │VOLUNTEER_REQUEST│
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

**Database Schema:**

**Database Schema:**
```json
{
  "id": "string (UUID)",
  "seek_request_id": "string (UUID)",
  "volunteer_request_id": "string (UUID)",
  "status": "string (pending|accepted|rejected|completed|cancelled)",
  "match_score": "float", // 1.0 indicates a match; not a ranked score
  "created_at": "datetime",
  "updated_at": "datetime",
  "communication": {
    "contact_exchanged": "boolean",
    "last_message_at": "datetime"
  },
  "completion": {
    "completed_at": "datetime"
  }
}
```

### 4. Calendar System

#### Calendar Event
Represents travel plans in the calendar view.

**Entity Relationship Diagram:**
```
┌─────────────────────────────────────────────────────────────────────┐
│                       CALENDAR_EVENT                               │
├─────────────────────────────────────────────────────────────────────┤
│ + id: UUID (PK)                                                     │
│ + user_id: UUID (FK → SEEKER|VOLUNTEER)                            │
│ + user_type: enum (seeker|volunteer)                               │
│ + request_id: UUID (FK → SEEK_REQUEST|VOLUNTEER_REQUEST)           │
│ + event_type: enum (seek|volunteer)                                │
│ + title: string                                                     │
│ + visibility: enum (public|private)                                │
│ + created_at: datetime                                              │
│ + updated_at: datetime                                              │
│                                                                     │
│ ┌─────────────── TRAVEL_DETAILS ──────────────┐                     │
│ │ + travel_time: datetime                     │                     │
│ │ + source_airport: string (IATA)             │                     │
│ │ + destination_airport: string (IATA)        │                     │
│ │ + airline: string                           │                     │
│ │ + flight_number: string                     │                     │
│ └─────────────────────────────────────────────┘                     │
│                                                                     │
│ ┌─────────────── TIME_FRAME ───────────────────┐                     │
│ │ + start_date: datetime                      │                     │
│ │ + end_date: datetime                        │                     │
│ │ + timezone: string                          │                     │
│ └─────────────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────┘

Calendar View Relationship:
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SEEKER    │─1:N─│ CALENDAR_EVENT  │─N:1─│ SEEK_REQUEST    │
└─────────────┘    └─────────────────┘    └─────────────────┘
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ VOLUNTEER   │─1:N─│ CALENDAR_EVENT  │─N:1─│VOLUNTEER_REQUEST│
└─────────────┘    └─────────────────┘    └─────────────────┘
```

**Database Schema:**
```json
{
  "id": "string (UUID)",
  "user_id": "string (UUID)",
  "user_type": "string (seeker|volunteer)",
  "request_id": "string (UUID)",
  "event_type": "string (seek|volunteer)",
  "title": "string",
  "travel_details": {
    "travel_time": "datetime",
    "source_airport": "string (IATA code)",
    "destination_airport": "string (IATA code)",
    "airline": "string",
    "flight_number": "string"
  },
  "time_frame": {
    "start_date": "datetime",
    "end_date": "datetime",
    "timezone": "string"
  },
  "visibility": "string (public|private)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## System Architecture & Request Flow Diagrams

### Overall System Architecture
```
┌─────────────────────────────────────────────────────────────────────────┐
│                        YATRA PLATFORM                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                       WEB CLIENT                                 │   │
│  │                                                                  │   │
│  │ • React/Vue/Angular                                              │   │
│  │ • Google OAuth Integration                                       │   │
│  │ • Responsive Design                                              │   │
│  │ • Calendar View                                                  │   │
│  │ • Real-time Notifications                                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    BACKEND SERVER                               │   │
│  │                                                                 │   │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │   │
│  │ │    AUTH     │ │   USERS     │ │  REQUESTS   │ │   MATCHES   │ │   │
│  │ │   SERVICE   │ │   SERVICE   │ │   SERVICE   │ │   SERVICE   │ │   │
│  │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │   │
│  │                                                                 │   │
│  │ ┌─────────────┐ ┌─────────────┐                                 │   │
│  │ │  CALENDAR   │ │NOTIFICATION │                                 │   │
│  │ │   SERVICE   │ │   SERVICE   │                                 │   │
│  │ └─────────────┘ └─────────────┘                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                    │
│                                    ▼                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      DATA LAYER                                 │   │
│  │                                                                 │   │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                 │   │
│  │ │   SQLite    │ │   Google    │ │   Email     │                 │   │
│  │ │ (Database)  │ │   OAuth     │ │  Service    │                 │   │
│  │ │             │ │             │ │             │                 │   │
│  │ └─────────────┘ └─────────────┘ └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### User Authentication Flow
```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   CLIENT    │         │   BACKEND   │         │   GOOGLE    │         │   SQLite    │
│             │         │   SERVER    │         │    OAUTH    │         │  DATABASE   │
└─────────────┘         └─────────────┘         └─────────────┘         └─────────────┘
       │                        │                        │                        │
       │ 1. Login with Google   │                        │                        │
       ├───────────────────────►│                        │                        │
       │                        │ 2. Verify Token        │                        │
       │                        ├───────────────────────►│                        │
       │                        │                        │                        │
       │                        │ 3. User Info           │                        │
       │                        │◄───────────────────────┤                        │
       │                        │                        │                        │
       │                        │ 4. Check/Create User   │                        │
       │                        ├────────────────────────┼───────────────────────►│
       │                        │                        │                        │
       │                        │ 5. User Data           │                        │
       │                        │◄───────────────────────┼───────────────────────┤
       │                        │                        │                        │
       │ 6. JWT + Refresh Token │                        │                        │
       │◄───────────────────────┤                        │                        │
       │                        │                        │                        │
```

### Seeker Request Flow (with Auto Matching)
```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐         ┌──────────────┐
│   SEEKER    │         │   REQUEST   │         │   MATCH     │         │ EMAIL NOTIFY │
│             │         │   SERVICE   │         │   SERVICE   │         │   SERVICE    │
└─────────────┘         └─────────────┘         └─────────────┘         └──────────────┘
       │                        │                        │                        │
       │ 1. Create Seek Request │                        │                        │
       ├───────────────────────►│                        │                        │
       │                        │ 2. Save Request        │                        │
       │                        │ 3. Add to Calendar     │                        │
       │                        │ 4. find_matches()      │                        │
       │                        ├───────────────────────►│                        │
       │                        │                        │ 5. Create Match       │
       │                        │◄───────────────────────┤    Records & Log      │
       │                        │                        │ 6. Notify Both Parties│
       │                        │                        ├───────────────────────►│
       │                        │                        │                        │
       │ 7. Response: Seek      │                        │                        │
       │    Request Created     │                        │                        │
       │    (no matches in body)│                        │                        │
       │◄───────────────────────┤                        │                        │
       │                        │                        │                        │
```

### Volunteer Request Flow (with Auto Matching)
```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐         ┌──────────────┐
│ VOLUNTEER   │         │   REQUEST   │         │   MATCH     │         │ EMAIL NOTIFY │
│             │         │   SERVICE   │         │   SERVICE   │         │   SERVICE    │
└─────────────┘         └─────────────┘         └─────────────┘         └──────────────┘
       │                        │                        │                        │
       │ 1. Create Volunteer    │                        │                        │
       │    Request             │                        │                        │
       ├───────────────────────►│                        │                        │
       │                        │ 2. Save Request        │                        │
       │                        │ 3. Add to Calendar     │                        │
       │                        │ 4. find_matches_for_   │                        │
       │                        │    volunteer()         │                        │
       │                        ├───────────────────────►│                        │
       │                        │                        │ 5. Create Match       │
       │                        │◄───────────────────────┤    Records & Log      │
       │                        │                        │ 6. Notify Both Parties│
       │                        │                        ├───────────────────────►│
       │                        │                        │                        │
       │ 7. Response: Volunteer │                        │                        │
       │    Request Created     │                        │                        │
       │    (no matches in body)│                        │                        │
       │◄───────────────────────┤                        │                        │
       │                        │                        │                        │
```

### Match Discovery & Acceptance Flow
`GET /api/matches/discover` displays persisted matches for the current user's
requests; it does not initiate matching or calculate a ranked list. Matching
runs when seeker or volunteer requests are created or updated.

The volunteer accepts a pending match with `POST /api/matches/{id}/accept`.
The seeker can then confirm with `POST /api/matches/{id}/confirm` or deny it
with `POST /api/matches/{id}/reject`. A volunteer can reject a pending match
with the same reject endpoint. Contact details are emailed to both parties
only after the seeker confirms.

### Complete Matching Process (Bi-directional)
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   SEEKER    │    │ VOLUNTEER   │    │   SYSTEM    │    │ EMAIL NOTIFY │    │   MATCH     │
│             │    │             │    │  ALGORITHM  │    │   SERVICE    │    │   CREATED   │
└─────────────┘    └─────────────┘    └─────────────┘    └──────────────┘    └─────────────┘
       │                   │                   │                   │                   │
       │ 1. Create         │                   │                   │                   │
       │ Seek Request      │                   │                   │                   │
       ├──────────────────►│                   │                   │                   │
       │                   │                   │                   │                   │
       │                   │                   │ 2A. find_matches()│                   │
       │                   │                   │ (for Seeker)      │                   │
       │                   │                   │ Find matching     │                   │
       │                   │                   │ volunteers        │                   │
       │                   │                   ├──────────────────►│                   │
       │                   │                   │ 3A. Create Match  │                   │
       │                   │                   │ records           │
       │                   │                   ├──────────────────►│                   │
       │                   │                   │ 4A. Notify both   │
       │                   │                   │ parties           │
       │ Response:         │                   │                   │
       │ SeekRequest       │                   │                   │                   │
       │ (no matches)      │                   │                   │                   │
       │◄──────────────────┤                   │                   │                   │
       │                   │                   │                   │                   │
       │                   │ 5. Create         │                   │                   │
       │                   │ Volunteer Request │                   │                   │
       │                   ├──────────────────►│                   │                   │
       │                   │                   │                   │                   │
       │                   │                   │ 2B. find_matches_ │                   │
       │                   │                   │ for_volunteer()   │                   │
       │                   │                   │ (for Volunteer)   │                   │
       │                   │                   │ Find matching     │                   │
       │                   │                   │ seekers           │                   │
       │                   │                   ├──────────────────►│                   │
       │                   │                   │ 3B. Create Match  │
       │                   │                   │ records           │
       │                   │                   ├──────────────────►│
       │                   │                   │ 4B. Notify both   │
       │                   │                   │ parties           │
       │ Response:         │                   │                   │
       │ VolunteerRequest  │                   │                   │                   │
       │ (no matches)      │                   │                   │                   │
       │                   │◄──────────────────┤                   │                   │
       │                   │                   │                   │                   │
       │ 6. Both check     │                   │                   │                   │
       │ /discover to see  │                   │                   │                   │
       │ matches           │                   │                   │                   │
       ├──────────────────────────────────────►│                   │                   │
       │                   ├──────────────────────────────────────►│                   │
       │                   │                   │                   │                   │
       │ 7. Volunteer accepts match            │                   │                   │
       ├─────────────────────────────────────────────────────────►│                   │
       │                   │                   │                   │                   │
       │ 8. Seeker confirms or denies          │                   │                   │
       ├─────────────────────────────────────────────────────────►│                   │
       │                   │                   │                   │                   │
       │ 9. Email contacts after confirmation  │                   │                   │
       │◄─────────────────────────────────────►│                   │                   │
       │                   │                   │                   │                   │
       │ 10. Travel        │                   │                   │                   │
       │ Assistance        │                   │                   │                   │
       │◄─────────────────►│                   │                   │                   │
       │                   │                   │                   │                   │
       │ 11. Mark Complete │                   │                   │                   │
       ├──────────────────►│                   │                   │                   │
```

## User Operations & API Specifications

### 1. Authentication APIs

#### Google OAuth Login/Register
**Endpoint:** `POST /api/auth/google`

**Input:**
```json
{
  "google_token": "string (Google OAuth ID token)",
  "user_type": "string (seeker|volunteer)",
  "profile": {
    "phone": "string (optional)",
    "preferred_language": "string",
    "emergency_contact": {
      "name": "string",
      "phone": "string",
      "email": "string"
    },
    // Additional fields for volunteer
    "languages_spoken": ["string"], // only for volunteer
    "experience_level": "string (beginner|intermediate|expert)", // only for volunteer
    "specialties": ["string"] // only for volunteer, e.g., ["elderly_assistance", "immigration_help"]
  }
}
```

**Output:**
```json
{
  "success": true,
  "data": {
    "user_id": "string (UUID)",
    "email": "string",
    "user_type": "string",
    "is_new_user": "boolean",
    "token": "string (JWT)",
    "profile": {
      "name": "string",
      "phone": "string",
      "preferred_language": "string",
      "google_picture": "string (URL to Google profile picture)"
    }
  },
  "message": "Authentication successful"
}
```

#### Refresh Token
**Endpoint:** `POST /api/auth/refresh`

**Input:**
```json
{
  "refresh_token": "string"
}
```

**Output:**
```json
{
  "success": true,
  "data": {
    "token": "string (new JWT)",
    "refresh_token": "string (new refresh token)"
  },
  "message": "Token refreshed successfully"
}
```

#### Logout
**Endpoint:** `POST /api/auth/logout`
**Authorization:** Bearer token

**Output:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### 2. Seeker Operations

#### Create Seek Request
**Endpoint:** `POST /api/requests/seek`
**Authorization:** Bearer token (seeker only)

**Input:**
```json
{
  "travel_details": {
    "travel_time": "datetime (ISO 8601)",
    "source_airport": "string (IATA code)",
    "destination_airport": "string (IATA code)",
    "airline": "string",
    "flight_number": "string",
    "number_of_people": "integer",
    "layover": {
      "has_layover": "boolean",
      "layover_airport": "string (optional)",
      "layover_duration": "integer (optional)"
    }
  },
  "assistance_needed": {
    "type": "string (travel_companion)",
    "categories": ["string"],
    "special_requirements": ["string"],
    "comments": "string"
  }
}
```

**Output:**
```json
{
  "success": true,
  "data": {
    "request_id": "string (UUID)",
    "status": "active",
    "travel_details": {
      "travel_time": "datetime",
      "source_airport": "string",
      "destination_airport": "string",
      "airline": "string",
      "flight_number": "string",
      "number_of_people": "integer"
    },
    "assistance_needed": {
      "type": "string",
      "categories": ["string"],
      "comments": "string"
    },
    "created_at": "datetime",
    "expires_at": "datetime"
  },
  "message": "Seek request created successfully"
}
```

#### List Seek Requests
**Endpoint:** `GET /api/requests/seek`
**Authorization:** Bearer token (seeker only)

**Query Parameters:**
- `status`: string (optional) - filter by status
- `page`: integer (optional) - pagination
- `limit`: integer (optional) - items per page

**Output:**
```json
{
  "success": true,
  "data": {
    "requests": [
      {
        "request_id": "string (UUID)",
        "status": "string",
        "travel_details": {
          "travel_time": "datetime",
          "source_airport": "string",
          "destination_airport": "string",
          "flight_number": "string"
        },
        "assistance_needed": {
          "type": "string",
          "categories": ["string"]
        },
        "matches_count": "integer",
        "created_at": "datetime"
      }
    ],
    "pagination": {
      "page": "integer",
      "limit": "integer",
      "total": "integer",
      "total_pages": "integer"
    }
  }
}
```

#### Get Seek Request Details
**Endpoint:** `GET /api/requests/seek/{request_id}`
**Authorization:** Bearer token (seeker only)

**Output:**
```json
{
  "success": true,
  "data": {
    "request_id": "string (UUID)",
    "status": "string",
    "travel_details": {
      "travel_time": "datetime",
      "source_airport": "string",
      "destination_airport": "string",
      "airline": "string",
      "flight_number": "string",
      "number_of_people": "integer",
      "layover": {
        "has_layover": "boolean",
        "layover_airport": "string",
        "layover_duration": "integer"
      }
    },
    "assistance_needed": {
      "type": "string",
      "categories": ["string"],
      "special_requirements": ["string"],
      "comments": "string"
    },
    "matches": [
      {
        "match_id": "string (UUID)",
        "volunteer": {
          "name": "string",
          "languages_spoken": ["string"]
        },
        "status": "string",
        "created_at": "datetime"
      }
    ],
    "created_at": "datetime",
    "expires_at": "datetime"
  }
}
```

#### Modify Seek Request
**Endpoint:** `PUT /api/requests/seek/{request_id}`
**Authorization:** Bearer token (seeker only)

**Input:** Same as Create Seek Request

**Output:**
```json
{
  "success": true,
  "data": {
    "request_id": "string (UUID)",
    "status": "string",
    "updated_at": "datetime"
  },
  "message": "Seek request updated successfully"
}
```

#### Delete Seek Request
**Endpoint:** `DELETE /api/requests/seek/{request_id}`
**Authorization:** Bearer token (seeker only)

**Output:**
```json
{
  "success": true,
  "message": "Seek request deleted successfully"
}
```

### 3. Volunteer Operations

#### Create Volunteer Request
**Endpoint:** `POST /api/requests/volunteer`
**Authorization:** Bearer token (volunteer only)

**Input:**
```json
{
  "travel_details": {
    "travel_time": "datetime (ISO 8601)",
    "source_airport": "string (IATA code)",
    "destination_airport": "string (IATA code)",
    "airline": "string",
    "flight_number": "string",
    "number_of_people": "integer",
    "layover": {
      "has_layover": "boolean",
      "layover_airport": "string (optional)",
      "layover_duration": "integer (optional)"
    }
  },
  "assistance_offered": {
    "types": ["string"],
    "categories": ["string"],
    "comments": "string"
  },
  "availability": {
    "flexible_timing": "boolean",
    "time_buffer": "integer"
  }
}
```

**Output:**
```json
{
  "success": true,
  "data": {
    "request_id": "string (UUID)",
    "status": "available",
    "travel_details": {
      "travel_time": "datetime",
      "source_airport": "string",
      "destination_airport": "string",
      "flight_number": "string"
    },
    "assistance_offered": {
      "types": ["string"],
      "categories": ["string"]
    },
    "created_at": "datetime",
    "expires_at": "datetime"
  },
  "message": "Volunteer request created successfully"
}
```

#### Volunteer Accepts Match
**Endpoint:** `POST /api/matches/{match_id}/accept`
**Authorization:** Bearer token (volunteer only)

**Output:**
```json
{
  "success": true,
  "data": {
    "match_id": "string (UUID)",
    "status": "accepted",
    "travel_details": {
      "travel_time": "datetime",
      "source_airport": "string",
      "destination_airport": "string",
      "flight_number": "string"
    }
  },
  "message": "Match accepted; seeker confirmation is still required"
}
```

#### Seeker Confirms Match
**Endpoint:** `POST /api/matches/{match_id}/confirm`
**Authorization:** seeker only; match must be volunteer-accepted

Contact details are emailed to both parties only after this confirmation.

#### Reject or Deny Match
**Endpoint:** `POST /api/matches/{match_id}/reject`
**Authorization:** volunteer for pending matches; seeker after volunteer acceptance

**Input:**
```json
{
  "reason": "string (optional)"
}
```

**Output:**
```json
{
  "success": true,
  "data": {
    "match_id": "string (UUID)",
    "status": "rejected"
  },
  "message": "Seek request rejected"
}
```

#### List/Get/Modify/Delete Volunteer Requests
Similar structure to seeker operations, with endpoints:
- `GET /api/requests/volunteer` - List volunteer requests
- `GET /api/requests/volunteer/{request_id}` - Get volunteer request details
- `PUT /api/requests/volunteer/{request_id}` - Modify volunteer request
- `DELETE /api/requests/volunteer/{request_id}` - Delete volunteer request

### 4. Calendar APIs

#### Get Calendar Events
**Endpoint:** `GET /api/calendar`
**Authorization:** Bearer token

**Query Parameters:**
- `start_date`: datetime (ISO 8601)
- `end_date`: datetime (ISO 8601)
- `event_type`: string (optional) - filter by seek/volunteer
- `airport`: string (optional) - filter by airport

**Output:**
```json
{
  "success": true,
  "data": {
    "events": [
      {
        "event_id": "string (UUID)",
        "event_type": "string (seek|volunteer)",
        "title": "string",
        "travel_details": {
          "travel_time": "datetime",
          "source_airport": "string",
          "destination_airport": "string",
          "flight_number": "string"
        },
        "time_frame": {
          "start_date": "datetime",
          "end_date": "datetime"
        },
        "user": {
          "name": "string (if public)",
          "user_type": "string"
        },
        "status": "string"
      }
    ],
    "time_frame": {
      "start_date": "datetime",
      "end_date": "datetime"
    }
  }
}
```

### 5. Matching & Discovery APIs

#### Find Matches
**Endpoint:** `GET /api/matches/discover`
**Authorization:** Bearer token

**Query Parameters:**
- `request_id`: string (UUID, optional) - display matches for a specific request

This endpoint returns persisted matches. Matching is triggered when a seeker
or volunteer request is created or updated; discovery does not initiate
matching or rank results.
**Output:**
```json
{
  "success": true,
  "data": {
    "matches": [
      {
        "match_id": "string (UUID)",
        "compatibility_score": "float",
        "request": {
          "request_id": "string (UUID)",
          "type": "string (seek|volunteer)",
          "travel_details": {
            "travel_time": "datetime",
            "source_airport": "string",
            "destination_airport": "string",
            "flight_number": "string"
          },
          "assistance": {
            "type": "string",
            "categories": ["string"]
          }
        },
        "user": {
          "name": "string",
          "languages_spoken": ["string"]
        },
        "created_at": "datetime"
      }
    ]
  }
}
```

---

## Error Response Format

All API endpoints follow a consistent error response format:

```json
{
  "success": false,
  "error": {
    "code": "string",
    "message": "string",
    "details": "object (optional)"
  }
}
```

**Common Error Codes:**
- `UNAUTHORIZED` - Invalid or missing Google OAuth token
- `FORBIDDEN` - User doesn't have permission for this operation
- `NOT_FOUND` - Requested resource doesn't exist
- `VALIDATION_ERROR` - Invalid input data
- `CONFLICT` - Operation conflicts with current state
- `RATE_LIMITED` - Too many requests
- `INTERNAL_ERROR` - Server error
- `GOOGLE_AUTH_ERROR` - Google authentication failed
- `TOKEN_EXPIRED` - JWT token has expired

---

## Data Flow Examples

### 1. Complete Seek Request Flow (Bi-directional Matching)

**Step-by-Step Process:**
```
[SEEKER] ──1. POST /api/requests/seek──► [API]
                                           │
                     ┌─────────────────────▼─────────────────────┐
                     │          REQUEST SERVICE                  │
                     │                                           │
                     │ 2. Validate & Save Seek Request           │
                     │ 3. Create Calendar Event                  │
                     │ 4. Call find_matches() Algorithm          │
                     │ 5. Persist Match Records                  │
                     │ 6. Notify Both Parties via Email          │
                     └─────────────────────┬─────────────────────┘
                                           │
[SEEKER] ◄──7. SeekRequest Created────────┘
            (no matches in response)

[VOLUNTEER] ──8. Creates volunteer request──────► [API]
                                                   │
                         ┌─────────────────────────▼─────────────────────┐
                         │          REQUEST SERVICE                      │
                         │                                               │
                         │ 9. Validate & Save Volunteer Request         │
                         │ 10. Create Calendar Event                    │
                         │ 11. Call find_matches_for_volunteer()        │
                         │ 12. Persist Match Records                    │
                         │ 13. Notify Both Parties via Email            │
                         └─────────────────────┬─────────────────────────┘
                                               │
[VOLUNTEER] ◄──14. VolunteerRequest Created───┘
              (no matches in response)

[SEEKER] ──15. GET /api/matches/discover──► [API]
                                             │
                 ┌───────────────────────────▼───────────────────────────┐
                 │          MATCH SERVICE                                │
                 │                                                       │
                 │ 16. Query Matches for Seeker's Requests             │
                 │ 17. Get Volunteer Details                           │
                 │ 18. Return Persisted Matches                        │
                 └───────────────────────────┬───────────────────────────┘
                                             │
[SEEKER] ◄──20. Available Matches List───────┘

[VOLUNTEER] ──21. GET /api/matches/discover──► [API]
                                                │
                   ┌─────────────────────────────▼─────────────────────────┐
                   │          MATCH SERVICE                                │
                   │                                                       │
                   │ 22. Query Matches for Volunteer's Requests          │
                   │ 23. Get Seeker Details                              │
                   │ 24. Return Persisted Matches                        │
                   └─────────────────────────────┬─────────────────────────┘
                                                │
[VOLUNTEER] ◄──26. Available Matches List───────┘

[VOLUNTEER] ──27. POST /api/matches/{id}/accept──► [API]
                                                          │
                              ┌──────────────────────────▼──────────────────────────┐
                              │             MATCH SERVICE                           │
                              │                                                     │
                              │ 28. Record volunteer acceptance                   │
                              │ 29. Seeker confirms or rejects                    │
                              │ 30. Exchange contacts only after confirmation      │
                              └──────────────────────────┬──────────────────────────┘
                                                        │
[SEEKER] ──POST /api/matches/{id}/confirm──► [API]
                                               │
                         Contacts emailed to both parties after confirmation
```

**Key Flow Steps:**

**Phase 1: Seeker Creates Request**
- `POST /api/requests/seek` → Seeker submits request
- `find_matches()` runs automatically
- Matching volunteers notified via email
- Match records created in database
- Response: `SeekRequest` (matches not included)

**Phase 2: Volunteer Creates Request**
- `POST /api/requests/volunteer` → Volunteer submits request
- `find_matches_for_volunteer()` runs automatically
- Matching seekers notified via email
- Match records created in database
- Response: `VolunteerRequest` (matches not included)

**Phase 3: Discovery**
- `GET /api/matches/discover` → Both parties view matches
- Seeker sees volunteers who can help (notified by email)
- Volunteer sees seekers who need help (notified by email)

**Phase 4: Match Acceptance**
- `POST /api/matches/{id}/accept` → Volunteer accepts a pending match
- Seeker confirms with `/confirm` or denies with `/reject`
- Contact details are exchanged only after seeker confirmation

### 2. Matching Algorithm Flow (Bi-directional)

**Smart Matching Process:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                      MATCHING ALGORITHM (Bi-directional)               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ ◄─── SCENARIO A: Seeker Creates Request ───►                          │
│                                                                         │
│ Input: New Seek Request                                                 │
│   ├─ Travel Details (Airport, Time, Flight)                            │
│   ├─ Assistance Needed (Categories, Requirements)                       │
│                                                                         │
│ Step 1A: find_matches() - Find Volunteer Matches                       │
│   ├─ Query all ACTIVE volunteer requests                               │
│   ├─ For each volunteer request:                                       │
│   │  ├─ Require the same source and destination airports                 │
│   │  ├─ Require the same non-empty flight number OR times within buffer │
│   │  ├─ If the predicate matches:                                       │
│   │  │  ├─ Create Match record (status: PENDING)                       │
│   │  │  ├─ Send match-found email to both parties                       │
│   │  │  │  ├─ Subject: "New Travel Assistance Match Found - Yatra"    │
│   │  │  │  └─ Call to action: Log in to discover matches              │
│   │  │  └─ Store match_score=1.0 as a match indicator                  │
│   │                                                                     │
│ ◄─── SCENARIO B: Volunteer Creates Request ───►                       │
│                                                                         │
│ Input: New Volunteer Request                                            │
│   ├─ Travel Details (Airport, Time, Flight)                            │
│   ├─ Assistance Offered (Categories, Skills)                           │
│                                                                         │
│ Step 1B: find_matches_for_volunteer() - Find Seeker Matches            │
│   ├─ Query all ACTIVE seek requests                                    │
│   ├─ For each seek request:                                            │
│   │  ├─ Apply the same route, flight-number, and time predicate          │
│   │  ├─ If the predicate matches:                                       │
│   │  │  ├─ Create Match record (status: PENDING)                       │
│   │  │  ├─ Send match-found email to both parties                       │
│   │  │  │  ├─ Subject: "New Travel Assistance Match Found - Yatra"    │
│   │  │  │  └─ Call to action: Log in to discover matches              │
│   │  │  └─ Store match_score=1.0 as a match indicator                  │
│                                                                         │
│ OUTPUT: Multiple Match Records                                          │
│   └─ Pending matches are available to both parties for review            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3. Calendar Integration Flow

**Calendar View Process:**
```
[USER] ──1. GET /api/calendar?start_date=X&end_date=Y──► [API]
                                                          │
                        ┌─────────────────────────────────▼─────────────────────────────────┐
                        │                    CALENDAR SERVICE                                │
                        │                                                                    │
                        │ 2. Query Requests in Date Range                                   │
                        │ 3. Query Matches in Date Range                                    │
                        │ 4. Aggregate Travel Events                                        │
                        │ 5. Apply Visibility Filters                                       │
                        │ 6. Format Calendar Data                                           │
                        └─────────────────────────────────┬─────────────────────────────────┘
                                                          │
[USER] ◄──7. Calendar Events with Travel Plans──────────┘

Visual Calendar Layout:
┌─────────────────────────────────────────────────────────────────────────┐
│                          CALENDAR VIEW                                 │
├─────────────────────────────────────────────────────────────────────────┤
│ Date: Jan 15, 2025                                                     │
│                                                                         │
│ ┌─────────────────────┐ ┌─────────────────────┐                        │
│ │   SEEK REQUEST      │ │  VOLUNTEER OFFER    │                        │
│ │                     │ │                     │                        │
│ │ CDG → BOM           │ │ CDG → BOM           │                        │
│ │ 14:30 - Air India   │ │ 14:45 - Air France  │                        │
│ │ Need: Immigration   │ │ Offer: Navigation   │                        │
│ │ Status: Active      │ │ Status: Available   │                        │
│ │                     │ │ Match Score: 85%    │                        │
│ └─────────────────────┘ └─────────────────────┘                        │
│                                                                         │
│ Date: Jan 16, 2025                                                     │
│                                                                         │
│ ┌─────────────────────┐                                                │
│ │     MATCHED         │                                                │
│ │                     │                                                │
│ │ JFK → DEL           │                                                │
│ │ 23:45 - Emirates    │                                                │
│ │ Assistance: Elderly │                                                │
│ │ Status: Confirmed   │                                                │
│ └─────────────────────┘                                                │
└─────────────────────────────────────────────────────────────────────────┘
```

**1. User creates request** → Request automatically added to calendar
**2. Calendar view shows travel plans** → `GET /api/calendar`
**3. Other users see public events** → Helps with discovery
**4. Matches appear on calendar** → Visual representation of connections

### 3. Matching Algorithm Flow

Matching is a boolean predicate, evaluated when a seeker or volunteer request
is created or updated:

1. Both requests must have the same source and destination airports.
2. They must have either the same non-empty flight number or departure times
   within `MATCH_TIME_BUFFER_HOURS` (default: four hours).
3. Each matching pair is persisted with `match_score=1.0`; there is no weighted
   score, threshold, or ranking. A newly persisted match triggers email
   notifications to both parties.

---

## Security Considerations

### Data Privacy
- Personal contact information only shared after both parties accept
- Option to use platform messaging before contact exchange
- Automatic data cleanup after travel completion

### User Safety
- User verification through Google OAuth
- Community self-moderation
- Reporting mechanism for inappropriate behavior
- Guidelines for safe meeting procedures

### API Security
- Google OAuth 2.0 for authentication
- JWT-based authorization with refresh tokens
- Input validation and sanitization
- HTTPS enforced for all communications
- Secure storage of refresh tokens (encrypted)
- Simple SQLite database for rapid development

### Google OAuth Integration
- Client-side Google Sign-In for web
- Server-side verification of Google ID tokens
- Automatic user profile creation from Google data
- Profile picture integration from Google accounts
- Seamless login/registration flow

---

This design provides a comprehensive foundation for implementing the Yatra platform's core functionality while maintaining flexibility for future enhancements and community growth.
