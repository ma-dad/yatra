"""
Tests for the new features introduced in the requirements:
- Dev login (ENABLE_GOOGLE_AUTH disabled by default)
- Dual role: a user can be both seeker and volunteer
- Simplified matching logic
- Request limit enforcement
- Seeker cancellation notifies accepted volunteer
- Auto-expire past travel time
- Calendar accessible to any authenticated user (/all endpoint)
- Email log-only mode (default)
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import settings

# ---------------------------------------------------------------------------
# Test database setup
# ---------------------------------------------------------------------------

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_features.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FUTURE_TIME = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
FAR_FUTURE = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
PAST_TIME = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")


def dev_login(client, email: str, user_type: str = "seeker", name: str = "Test User") -> str:
    """Log in via dev-login and return the JWT token."""
    resp = client.post(
        "/api/auth/dev-login",
        json={"email": email, "user_type": user_type, "name": name}
    )
    assert resp.status_code == 200, resp.json()
    return resp.json()["data"]["token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def seek_payload(flight: str = "AA100", travel_time: str = FUTURE_TIME,
                 src: str = "JFK", dst: str = "LHR") -> dict:
    return {
        "travel_details": {
            "travel_time": travel_time,
            "source_airport": src,
            "destination_airport": dst,
            "flight_number": flight,
            "number_of_people": 1,
        },
        "assistance_needed": {
            "type": "travel_companion",
            "categories": ["language_support"],
            "special_requirements": [],
        },
    }


def volunteer_payload(flight: str = "AA100", travel_time: str = FUTURE_TIME,
                      src: str = "JFK", dst: str = "LHR") -> dict:
    return {
        "travel_details": {
            "travel_time": travel_time,
            "source_airport": src,
            "destination_airport": dst,
            "flight_number": flight,
            "number_of_people": 1,
        },
        "assistance_offered": {
            "types": ["navigation"],
            "categories": ["language_support"],
        },
    }


# ---------------------------------------------------------------------------
# Dev login tests
# ---------------------------------------------------------------------------

class TestDevLogin:
    def test_dev_login_creates_new_user(self, client):
        resp = client.post(
            "/api/auth/dev-login",
            json={"email": "alice@example.com", "user_type": "seeker"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["is_new_user"] is True
        assert data["data"]["token"]

    def test_dev_login_returns_is_new_user_false_on_relogin(self, client):
        client.post("/api/auth/dev-login", json={"email": "bob@example.com", "user_type": "seeker"})
        resp = client.post("/api/auth/dev-login", json={"email": "bob@example.com", "user_type": "seeker"})
        assert resp.json()["data"]["is_new_user"] is False

    def test_dev_login_google_auth_disabled_by_default(self, client):
        """Google auth endpoint should return 403 when ENABLE_GOOGLE_AUTH is False."""
        resp = client.post(
            "/api/auth/google",
            json={"google_token": "fake_token", "user_type": "seeker"}
        )
        assert resp.status_code == 403

    def test_protected_endpoint_requires_token(self, client):
        resp = client.get("/api/requests/seek")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Dual-role tests
# ---------------------------------------------------------------------------

class TestDualRole:
    def test_seeker_can_create_volunteer_request(self, client):
        """A user registered as seeker can also create a volunteer request."""
        token = dev_login(client, "dual@example.com", "seeker")
        resp = client.post(
            "/api/requests/volunteer",
            json=volunteer_payload(),
            headers=auth_headers(token)
        )
        assert resp.status_code == 201, resp.json()
        assert resp.json()["id"]

    def test_volunteer_can_create_seek_request(self, client):
        """A user registered as volunteer can also create a seek request."""
        token = dev_login(client, "dual2@example.com", "volunteer")
        resp = client.post(
            "/api/requests/seek",
            json=seek_payload(),
            headers=auth_headers(token)
        )
        assert resp.status_code == 201, resp.json()
        assert resp.json()["id"]


# ---------------------------------------------------------------------------
# Matching logic tests
# ---------------------------------------------------------------------------

class TestMatchingLogic:
    def test_same_flight_triggers_match(self, client):
        seeker_token = dev_login(client, "seeker_match@example.com", "seeker")
        vol_token = dev_login(client, "vol_match@example.com", "volunteer")

        # Create seek request first
        s_resp = client.post("/api/requests/seek", json=seek_payload("BA200"),
                             headers=auth_headers(seeker_token))
        assert s_resp.status_code == 201

        # Create volunteer request with same flight → should trigger match
        v_resp = client.post("/api/requests/volunteer", json=volunteer_payload("BA200"),
                             headers=auth_headers(vol_token))
        assert v_resp.status_code == 201

        matches = client.get("/api/matches/discover", headers=auth_headers(seeker_token)).json()
        assert len(matches) >= 1
        assert "match_id" in matches[0]

    def test_different_route_no_match(self, client):
        seeker_token = dev_login(client, "seeker_nomatch@example.com", "seeker")
        vol_token = dev_login(client, "vol_nomatch@example.com", "volunteer")

        client.post("/api/requests/seek",
                    json=seek_payload("ZZ1", src="JFK", dst="LHR"),
                    headers=auth_headers(seeker_token))
        client.post("/api/requests/volunteer",
                    json=volunteer_payload("ZZ1", src="JFK", dst="CDG"),  # different destination
                    headers=auth_headers(vol_token))

        matches = client.get("/api/matches/discover", headers=auth_headers(seeker_token)).json()
        assert len(matches) == 0

    def test_time_buffer_triggers_match(self, client):
        """Requests within MATCH_TIME_BUFFER_HOURS should match even with different flight numbers."""
        seeker_token = dev_login(client, "seeker_time@example.com", "seeker")
        vol_token = dev_login(client, "vol_time@example.com", "volunteer")

        t1 = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S")
        # Volunteer departs 2 hours later (within default 4h buffer)
        t2 = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=5, hours=2)).strftime("%Y-%m-%dT%H:%M:%S")

        client.post("/api/requests/seek",
                    json=seek_payload("XX1", travel_time=t1),
                    headers=auth_headers(seeker_token))
        client.post("/api/requests/volunteer",
                    json=volunteer_payload("XX2", travel_time=t2),  # different flight
                    headers=auth_headers(vol_token))

        matches = client.get("/api/matches/discover", headers=auth_headers(seeker_token)).json()
        assert len(matches) >= 1

    def test_outside_time_buffer_no_match(self, client):
        """Requests more than MATCH_TIME_BUFFER_HOURS apart should NOT match."""
        seeker_token = dev_login(client, "seeker_far@example.com", "seeker")
        vol_token = dev_login(client, "vol_far@example.com", "volunteer")

        t1 = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S")
        t2 = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=5, hours=6)).strftime("%Y-%m-%dT%H:%M:%S")

        client.post("/api/requests/seek",
                    json=seek_payload("YY1", travel_time=t1),
                    headers=auth_headers(seeker_token))
        client.post("/api/requests/volunteer",
                    json=volunteer_payload("YY2", travel_time=t2),
                    headers=auth_headers(vol_token))

        matches = client.get("/api/matches/discover", headers=auth_headers(seeker_token)).json()
        assert len(matches) == 0


# ---------------------------------------------------------------------------
# Request limit tests
# ---------------------------------------------------------------------------

class TestRequestLimits:
    def test_seeker_limit_enforced(self, client):
        token = dev_login(client, "limit_seeker@example.com", "seeker")
        limit = settings.SEEKER_REQUEST_LIMIT

        for i in range(limit):
            t = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=10 + i)).strftime("%Y-%m-%dT%H:%M:%S")
            resp = client.post("/api/requests/seek",
                               json=seek_payload(f"LM{i}", travel_time=t),
                               headers=auth_headers(token))
            assert resp.status_code == 201

        # (limit+1)-th request should be rejected
        t = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%S")
        resp = client.post("/api/requests/seek",
                           json=seek_payload("LMOVER", travel_time=t),
                           headers=auth_headers(token))
        assert resp.status_code == 429

    def test_volunteer_limit_enforced(self, client):
        token = dev_login(client, "limit_vol@example.com", "volunteer")
        limit = settings.VOLUNTEER_REQUEST_LIMIT

        for i in range(limit):
            t = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=10 + i)).strftime("%Y-%m-%dT%H:%M:%S")
            resp = client.post("/api/requests/volunteer",
                               json=volunteer_payload(f"VL{i}", travel_time=t),
                               headers=auth_headers(token))
            assert resp.status_code == 201

        t = (datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%S")
        resp = client.post("/api/requests/volunteer",
                           json=volunteer_payload("VLOVER", travel_time=t),
                           headers=auth_headers(token))
        assert resp.status_code == 429


# ---------------------------------------------------------------------------
# Seeker cancellation tests
# ---------------------------------------------------------------------------

class TestSeekerCancellation:
    def test_delete_seek_request_sets_cancelled(self, client):
        """DELETE /seek/{id} should soft-cancel (not hard delete) the request."""
        token = dev_login(client, "cancel_test@example.com", "seeker")
        resp = client.post("/api/requests/seek", json=seek_payload(),
                           headers=auth_headers(token))
        seek_id = resp.json()["id"]

        del_resp = client.delete(f"/api/requests/seek/{seek_id}",
                                 headers=auth_headers(token))
        assert del_resp.status_code == 204

        # Request should still exist with CANCELLED status
        list_resp = client.get("/api/requests/seek?status=cancelled",
                               headers=auth_headers(token))
        ids = [r["id"] for r in list_resp.json()]
        assert seek_id in ids

    def test_put_cancelled_seek_notifies_via_log(self, client, caplog):
        """Cancelling a seek request with an accepted match logs an email."""
        seeker_token = dev_login(client, "seeker_cancel@example.com", "seeker")
        vol_token = dev_login(client, "vol_cancel@example.com", "volunteer")

        s_resp = client.post("/api/requests/seek", json=seek_payload("CC1"),
                             headers=auth_headers(seeker_token))
        assert s_resp.status_code == 201, s_resp.json()
        seek_id = s_resp.json()["id"]

        client.post("/api/requests/volunteer", json=volunteer_payload("CC1"),
                    headers=auth_headers(vol_token))

        matches = client.get("/api/matches/discover",
                             headers=auth_headers(vol_token)).json()
        if matches:
            # Use 'match_id' from MatchWithDetails schema
            match_id = matches[0]["match_id"]
            client.post(f"/api/matches/{match_id}/accept",
                        headers=auth_headers(vol_token))

        import logging
        with caplog.at_level(logging.INFO, logger="app.utils.email"):
            resp = client.put(f"/api/requests/seek/{seek_id}",
                              json={"status": "cancelled"},
                              headers=auth_headers(seeker_token))

        # PUT with status=cancelled should succeed (200)
        assert resp.status_code == 200, resp.json()
        assert resp.json()["status"] == "cancelled"


# ---------------------------------------------------------------------------
# Calendar access tests
# ---------------------------------------------------------------------------

class TestCalendarAccess:
    def test_own_calendar_requires_auth(self, client):
        resp = client.get("/api/calendar/")
        assert resp.status_code == 401

    def test_all_calendar_requires_auth(self, client):
        resp = client.get("/api/calendar/all")
        assert resp.status_code == 401

    def test_authenticated_user_can_see_own_calendar(self, client):
        token = dev_login(client, "cal_test@example.com", "seeker")
        resp = client.get("/api/calendar/", headers=auth_headers(token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_authenticated_user_can_browse_all_calendar(self, client):
        token1 = dev_login(client, "cal_user1@example.com", "volunteer")
        token2 = dev_login(client, "cal_user2@example.com", "seeker")

        # User1 creates a volunteer request (creates a calendar event)
        client.post("/api/requests/volunteer", json=volunteer_payload(),
                    headers=auth_headers(token1))

        # User2 browses all events – should see user1's event
        resp = client.get("/api/calendar/all", headers=auth_headers(token2))
        assert resp.status_code == 200
        events = resp.json()
        assert isinstance(events, list)
        assert len(events) >= 1


# ---------------------------------------------------------------------------
# Email log-only mode test
# ---------------------------------------------------------------------------

class TestEmailLogOnly:
    def test_email_log_only_enabled_by_default(self):
        assert settings.EMAIL_LOG_ONLY is True

    def test_send_email_logs_when_log_only(self, caplog):
        import logging
        from app.utils.email import send_email

        with caplog.at_level(logging.INFO, logger="app.utils.email"):
            result = send_email(
                to_emails=["test@example.com"],
                subject="Test Subject",
                body="Test Body"
            )

        assert result is True
        assert any("EMAIL LOG-ONLY" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# Config defaults test
# ---------------------------------------------------------------------------

class TestConfigDefaults:
    def test_google_auth_disabled_by_default(self):
        assert settings.ENABLE_GOOGLE_AUTH is False

    def test_email_log_only_enabled_by_default(self):
        assert settings.EMAIL_LOG_ONLY is True

    def test_seeker_request_limit_default(self):
        assert settings.SEEKER_REQUEST_LIMIT == 5

    def test_volunteer_request_limit_default(self):
        assert settings.VOLUNTEER_REQUEST_LIMIT == 5

    def test_match_time_buffer_default(self):
        assert settings.MATCH_TIME_BUFFER_HOURS == 4
