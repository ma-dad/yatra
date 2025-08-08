# Yatra Platform - System Design & API Specification

## Overview
This document defines the complete system design for the Yatra community travel assistance platform, including data structures, user operations, and API specifications for connecting travelers who need help with volunteers who can assist them.

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
  "match_score": "float", // algorithm-calculated compatibility score
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

### Seeker Request Flow
```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   SEEKER    │         │   REQUEST   │         │   MATCH     │         │  CALENDAR   │
│             │         │   SERVICE   │         │   SERVICE   │         │   SERVICE   │
└─────────────┘         └─────────────┘         └─────────────┘         └─────────────┘
       │                        │                        │                        │
       │ 1. Create Seek Request │                        │                        │
       ├───────────────────────►│                        │                        │
       │                        │ 2. Save Request        │                        │
       │                        │ 3. Add to Calendar     │                        │
       │                        ├────────────────────────┼───────────────────────►│
       │                        │                        │                        │
       │                        │ 4. Find Matches        │                        │
       │                        ├───────────────────────►│                        │
       │                        │                        │                        │
       │                        │ 5. Notify Volunteers   │                        │
       │                        │◄───────────────────────┤                        │
       │                        │                        │                        │
       │ 6. Request Created     │                        │                        │
       │◄───────────────────────┤                        │                        │
       │                        │                        │                        │
       │ 7. View Matches        │                        │                        │
       ├───────────────────────►│                        │                        │
       │                        │ 8. Get Matches         │                        │
       │                        ├───────────────────────►│                        │
       │                        │                        │                        │
       │ 9. Match List          │ 10. Match Data         │                        │
       │◄───────────────────────┤◄───────────────────────┤                        │
```

### Volunteer Response Flow
```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│ VOLUNTEER   │         │   MATCH     │         │NOTIFICATION │         │   SEEKER    │
│             │         │   SERVICE   │         │   SERVICE   │         │             │
└─────────────┘         └─────────────┘         └─────────────┘         └─────────────┘
       │                        │                        │                        │
       │ 1. View Available      │                        │                        │
       │    Seek Requests       │                        │                        │
       ├───────────────────────►│                        │                        │
       │                        │                        │                        │
       │ 2. Available Matches   │                        │                        │
       │◄───────────────────────┤                        │                        │
       │                        │                        │                        │
       │ 3. Accept Match        │                        │                        │
       ├───────────────────────►│                        │                        │
       │                        │ 4. Update Status       │                        │
       │                        │ 5. Exchange Contacts   │                        │
       │                        │                        │                        │
       │                        │ 6. Notify Seeker       │                        │
       │                        ├───────────────────────►│                        │
       │                        │                        │ 7. Send Notification   │
       │                        │                        ├───────────────────────►│
       │                        │                        │                        │
       │ 8. Contact Details     │                        │                        │
       │◄───────────────────────┤                        │                        │
       │                        │                        │                        │
```

### Complete Matching Process
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   SEEKER    │    │ VOLUNTEER   │    │   SYSTEM    │    │   MATCH     │
│             │    │             │    │  ALGORITHM  │    │   CREATED   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       │ 1. Create         │                   │                   │
       │ Seek Request      │                   │                   │
       ├──────────────────►│                   │                   │
       │                   │                   │                   │
       │                   │ 2. Create         │                   │
       │                   │ Volunteer Request │                   │
       │                   ├──────────────────►│                   │
       │                   │                   │                   │
       │                   │                   │ 3. Match          │
       │                   │                   │ Algorithm         │
       │                   │                   │ (Airport, Time,   │
       │                   │                   │ Language, etc.)   │
       │                   │                   ├──────────────────►│
       │                   │                   │                   │
       │                   │ 4. Notify Match   │                   │
       │                   │◄─────────────────────────────────────┤
       │                   │                   │                   │
       │                   │ 5. Accept/Reject  │                   │
       │                   ├─────────────────────────────────────►│
       │                   │                   │                   │
       │ 6. Contact        │                   │                   │
       │ Exchange          │                   │                   │
       │◄─────────────────►│                   │                   │
       │                   │                   │                   │
       │ 7. Travel         │                   │                   │
       │ Assistance        │                   │                   │
       │◄─────────────────►│                   │                   │
       │                   │                   │                   │
       │ 8. Mark Complete  │                   │                   │
       ├─────────────────────────────────────────────────────────►│
       │                   │                   │                   │
       │                   │ 9. Mark Complete  │                   │
       │                   ├─────────────────────────────────────►│
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

#### Accept Seek Request
**Endpoint:** `POST /api/matches/{match_id}/accept`
**Authorization:** Bearer token (volunteer only)

**Output:**
```json
{
  "success": true,
  "data": {
    "match_id": "string (UUID)",
    "status": "accepted",
    "seeker_contact": {
      "name": "string",
      "email": "string",
      "phone": "string"
    },
    "travel_details": {
      "travel_time": "datetime",
      "source_airport": "string",
      "destination_airport": "string",
      "flight_number": "string"
    }
  },
  "message": "Seek request accepted successfully"
}
```

#### Reject Seek Request
**Endpoint:** `POST /api/matches/{match_id}/reject`
**Authorization:** Bearer token (volunteer only)

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
- `request_id`: string (UUID) - find matches for specific request
- `airport`: string (optional) - filter by airport
- `date_range`: string (optional) - filter by date range

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

### 1. Complete Seek Request Flow

**Step-by-Step Process:**
```
[SEEKER] ──1. POST /api/requests/seek──► [API]
                                           │
                     ┌─────────────────────▼─────────────────────┐
                     │          REQUEST SERVICE                  │
                     │                                           │
                     │ 2. Validate & Save Request                │
                     │ 3. Create Calendar Event                  │
                     │ 4. Run Matching Algorithm                 │
                     │ 5. Notify Potential Volunteers            │
                     └─────────────────────┬─────────────────────┘
                                           │
[SEEKER] ◄──6. Request Created Response───┘

[VOLUNTEER] ──7. GET /api/matches/discover──► [API]
                                               │
                         ┌─────────────────────▼─────────────────────┐
                         │          MATCH SERVICE                    │
                         │                                           │
                         │ 8. Find Compatible Requests              │
                         │ 9. Calculate Match Scores                │
                         │ 10. Return Ranked Matches                │
                         └─────────────────────┬─────────────────────┘
                                               │
[VOLUNTEER] ◄──11. Available Matches List─────┘

[VOLUNTEER] ──12. POST /api/matches/{id}/accept──► [API]
                                                     │
                            ┌────────────────────────▼────────────────────────┐
                            │             MATCH SERVICE                       │
                            │                                                 │
                            │ 13. Update Match Status                        │
                            │ 14. Exchange Contact Information               │
                            │ 15. Notify Seeker                             │
                            │ 16. Update Calendar Events                     │
                            └────────────────────────┬────────────────────────┘
                                                     │
[VOLUNTEER] ◄──17. Contact Exchange Successful──────┘
```

**1. Seeker creates request** → `POST /api/requests/seek`
**2. System finds potential matches** → Background matching algorithm
**3. Volunteer sees match** → `GET /api/matches/discover`
**4. Volunteer accepts match** → `POST /api/matches/{match_id}/accept`
**5. Contact details exchanged** → Both parties get contact info
**6. Travel assistance completed** → Users can mark assistance as complete
**7. Request marked complete** → `POST /api/matches/{match_id}/complete`

### 2. Calendar Integration Flow

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

**Smart Matching Process:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                      MATCHING ALGORITHM                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ Input: New Seek Request                                                 │
│   ├─ Travel Details (Airport, Time, Flight)                            │
│   ├─ Assistance Needed (Categories, Requirements)                       │
│   └─ User Profile (Language, Preferences)                              │
│                                                                         │
│ Step 1: Primary Filters                                                │
│   ├─ Same Route (Source → Destination)                                 │
│   ├─ Time Window (±4 hours)                                            │
│   ├─ Available Volunteers                                               │
│   └─ Active Requests Only                                               │
│                                                                         │
│ Step 2: Compatibility Scoring                                          │
│   ├─ Route Match: 40 points                                            │
│   ├─ Time Proximity: 30 points                                         │
│   ├─ Language Match: 20 points                                         │
│   ├─ Category Match: 10 points                                         │
│   └─ Total Score: 0-100                                                │
│                                                                         │
│ Step 3: Ranking & Notification                                         │
│   ├─ Sort by Score (Highest First)                                     │
│   ├─ Apply Business Rules                                               │
│   ├─ Notify Top 5 Volunteers                                           │
│   └─ Store Matches in Database                                          │
│                                                                         │
│ Output: Ranked Match List                                               │
│   └─ Ready for Volunteer Review                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Security Considerations

### Data Privacy
- Personal contact information only shared after match acceptance
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
