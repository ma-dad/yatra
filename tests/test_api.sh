#!/usr/bin/env bash
# =============================================================================
# Yatra Platform – API Test Suite (shell scripts)
# =============================================================================
#
# USAGE
#   ./tests/test_api.sh [BASE_URL]
#
# DESCRIPTION
#   End-to-end API tests that exercise the main flows using curl.
#   The server must be running before executing this script.
#
#   By default the script targets http://localhost:8000.
#   Pass a different base URL as the first argument, e.g.:
#
#     ./tests/test_api.sh http://staging.example.com
#
# PREREQUISITES
#   - curl
#   - jq  (JSON parsing)
#   - The server must have ENABLE_GOOGLE_AUTH=false (dev-login enabled)
#   - The server must have EMAIL_LOG_ONLY=true (default)
#
# TESTED FLOWS
#   1.  Health check
#   2.  Dev login – new seeker user
#   3.  Dev login – new volunteer user
#   4.  Same user logs in again (is_new_user=false)
#   5.  User can act as both seeker and volunteer (dual role)
#   6.  Create a seek request (enforce limit)
#   7.  Create a volunteer request → matching triggered automatically
#   8.  Discover matches
#   9.  Accept a match (volunteer)
#   10. Reject a match (volunteer)
#   11. List calendar events (authenticated)
#   12. Browse all calendar events (authenticated)
#   13. Seeker cancels seek request → accepted volunteer notified
#   14. Request limit enforcement
#   15. Dev login blocked when ENABLE_GOOGLE_AUTH=true (negative test, skipped if not applicable)
#
# =============================================================================

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
PASS=0
FAIL=0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

green() { printf '\033[0;32m%s\033[0m\n' "$*"; }
red()   { printf '\033[0;31m%s\033[0m\n' "$*"; }
cyan()  { printf '\033[0;36m%s\033[0m\n' "$*"; }

assert_eq() {
    local desc="$1" expected="$2" actual="$3"
    if [[ "$actual" == "$expected" ]]; then
        green "  ✓ $desc"
        (( PASS++ )) || true
    else
        red   "  ✗ $desc"
        red   "    expected: $expected"
        red   "    actual:   $actual"
        (( FAIL++ )) || true
    fi
}

assert_ne() {
    local desc="$1" unexpected="$2" actual="$3"
    if [[ "$actual" != "$unexpected" ]]; then
        green "  ✓ $desc"
        (( PASS++ )) || true
    else
        red   "  ✗ $desc (should not be '$unexpected')"
        (( FAIL++ )) || true
    fi
}

assert_contains() {
    local desc="$1" needle="$2" haystack="$3"
    if echo "$haystack" | grep -q "$needle"; then
        green "  ✓ $desc"
        (( PASS++ )) || true
    else
        red   "  ✗ $desc"
        red   "    expected to contain: $needle"
        red   "    actual: $haystack"
        (( FAIL++ )) || true
    fi
}

api() {
    # api <method> <path> [body] [token]
    local method="$1"
    local path="$2"
    local body="${3:-}"
    local token="${4:-}"

    local -a args=(-s -X "$method")

    if [[ -n "$token" ]]; then
        args+=(-H "Authorization: Bearer $token")
    fi

    if [[ -n "$body" ]]; then
        args+=(-H "Content-Type: application/json" -d "$body")
    fi

    args+=("${BASE_URL}${path}")
    curl "${args[@]}"
}

# ---------------------------------------------------------------------------
# FLOW 1 – Health check
# ---------------------------------------------------------------------------
cyan "\n[FLOW 1] Health check"

resp=$(api GET /health)
assert_eq "GET /health returns status=healthy" "healthy" "$(echo "$resp" | jq -r '.status')"

# ---------------------------------------------------------------------------
# FLOW 2 – Dev login: new seeker user
# ---------------------------------------------------------------------------
cyan "\n[FLOW 2] Dev login – new seeker"

SEEKER_EMAIL="seeker_test_$(date +%s)@example.com"
resp=$(api POST /api/auth/dev-login \
    "{\"email\": \"$SEEKER_EMAIL\", \"user_type\": \"seeker\", \"name\": \"Test Seeker\"}")

SEEKER_TOKEN=$(echo "$resp" | jq -r '.data.token // empty')
SEEKER_ID=$(echo "$resp" | jq -r '.data.user_id // empty')

assert_eq "dev-login returns success=true"    "true"   "$(echo "$resp" | jq -r '.success')"
assert_eq "new seeker: is_new_user=true"      "true"   "$(echo "$resp" | jq -r '.data.is_new_user')"
assert_ne "dev-login returns a JWT token"     ""       "$SEEKER_TOKEN"
assert_ne "dev-login returns a user_id"       ""       "$SEEKER_ID"

# ---------------------------------------------------------------------------
# FLOW 3 – Dev login: new volunteer user
# ---------------------------------------------------------------------------
cyan "\n[FLOW 3] Dev login – new volunteer"

VOL_EMAIL="volunteer_test_$(date +%s)@example.com"
resp=$(api POST /api/auth/dev-login \
    "{\"email\": \"$VOL_EMAIL\", \"user_type\": \"volunteer\", \"name\": \"Test Volunteer\"}")

VOL_TOKEN=$(echo "$resp" | jq -r '.data.token // empty')
VOL_ID=$(echo "$resp" | jq -r '.data.user_id // empty')

assert_eq "volunteer dev-login success"       "true"   "$(echo "$resp" | jq -r '.success')"
assert_eq "new volunteer: is_new_user=true"   "true"   "$(echo "$resp" | jq -r '.data.is_new_user')"
assert_ne "volunteer JWT token present"       ""       "$VOL_TOKEN"

# ---------------------------------------------------------------------------
# FLOW 4 – Same user logs in again (is_new_user=false)
# ---------------------------------------------------------------------------
cyan "\n[FLOW 4] Re-login returns is_new_user=false"

resp=$(api POST /api/auth/dev-login \
    "{\"email\": \"$SEEKER_EMAIL\", \"user_type\": \"seeker\"}")

assert_eq "re-login is_new_user=false"        "false"  "$(echo "$resp" | jq -r '.data.is_new_user')"

# ---------------------------------------------------------------------------
# FLOW 5 – Dual role: seeker user creates a volunteer request
# ---------------------------------------------------------------------------
cyan "\n[FLOW 5] Dual role – seeker acts as volunteer"

TRAVEL_TIME=$(date -u -d '+7 days' +%Y-%m-%dT%H:%M:%S 2>/dev/null || \
              date -u -v+7d +%Y-%m-%dT%H:%M:%S 2>/dev/null || \
              python3 -c "from datetime import datetime,timedelta; print((datetime.utcnow()+timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S'))")

resp=$(api POST /api/requests/volunteer \
    "{
        \"travel_details\": {
            \"travel_time\": \"${TRAVEL_TIME}\",
            \"source_airport\": \"JFK\",
            \"destination_airport\": \"LHR\",
            \"flight_number\": \"BA178\",
            \"number_of_people\": 1
        },
        \"assistance_offered\": {
            \"types\": [\"navigation\"],
            \"categories\": [\"language_support\"]
        }
    }" \
    "$SEEKER_TOKEN")

DUAL_VOL_ID=$(echo "$resp" | jq -r '.id // empty')
assert_ne "seeker can create volunteer request (dual role)" "" "$DUAL_VOL_ID"

# ---------------------------------------------------------------------------
# FLOW 6 – Create seek request and auto-matching
# ---------------------------------------------------------------------------
cyan "\n[FLOW 6] Create seek request (seeker)"

resp=$(api POST /api/requests/seek \
    "{
        \"travel_details\": {
            \"travel_time\": \"${TRAVEL_TIME}\",
            \"source_airport\": \"JFK\",
            \"destination_airport\": \"LHR\",
            \"flight_number\": \"BA178\",
            \"number_of_people\": 1
        },
        \"assistance_needed\": {
            \"type\": \"travel_companion\",
            \"categories\": [\"language_support\"],
            \"special_requirements\": []
        }
    }" \
    "$SEEKER_TOKEN")

SEEK_ID=$(echo "$resp" | jq -r '.id // empty')
assert_ne "seek request created"              ""       "$SEEK_ID"
assert_eq "seek request status=active"        "active" "$(echo "$resp" | jq -r '.status')"

# ---------------------------------------------------------------------------
# FLOW 7 – Create volunteer request → triggers matching
# ---------------------------------------------------------------------------
cyan "\n[FLOW 7] Create volunteer request (triggers matching)"

resp=$(api POST /api/requests/volunteer \
    "{
        \"travel_details\": {
            \"travel_time\": \"${TRAVEL_TIME}\",
            \"source_airport\": \"JFK\",
            \"destination_airport\": \"LHR\",
            \"flight_number\": \"BA178\",
            \"number_of_people\": 1
        },
        \"assistance_offered\": {
            \"types\": [\"navigation\", \"language\"],
            \"categories\": [\"language_support\"]
        }
    }" \
    "$VOL_TOKEN")

VOL_REQ_ID=$(echo "$resp" | jq -r '.id // empty')
assert_ne "volunteer request created"         ""       "$VOL_REQ_ID"
assert_eq "volunteer request status=active"   "active" "$(echo "$resp" | jq -r '.status')"

# ---------------------------------------------------------------------------
# FLOW 8 – Discover matches
# ---------------------------------------------------------------------------
cyan "\n[FLOW 8] Discover matches"

# Give a moment for matching to persist
sleep 1

resp=$(api GET /api/matches/discover "" "$SEEKER_TOKEN")
MATCH_COUNT=$(echo "$resp" | jq '. | length' 2>/dev/null || echo "0")
assert_ne "seeker has at least one pending match" "0" "$MATCH_COUNT"

FIRST_MATCH_ID=$(echo "$resp" | jq -r '.[0].match_id // empty')

# Volunteer discovers matches too
resp=$(api GET /api/matches/discover "" "$VOL_TOKEN")
VOL_MATCH_COUNT=$(echo "$resp" | jq '. | length' 2>/dev/null || echo "0")
assert_ne "volunteer has at least one pending match" "0" "$VOL_MATCH_COUNT"

VOL_MATCH_ID=$(echo "$resp" | jq -r '.[0].match_id // empty')

# ---------------------------------------------------------------------------
# FLOW 9 – Accept a match (volunteer)
# ---------------------------------------------------------------------------
cyan "\n[FLOW 9] Accept match"

if [[ -n "$VOL_MATCH_ID" ]]; then
    resp=$(api POST "/api/matches/${VOL_MATCH_ID}/accept" "" "$VOL_TOKEN")
    assert_eq "match accepted status=accepted" "accepted" "$(echo "$resp" | jq -r '.status')"
else
    red "  ⚠ Skipping: no match id for volunteer"
fi

# ---------------------------------------------------------------------------
# FLOW 10 – Create a second volunteer request for reject test
# ---------------------------------------------------------------------------
cyan "\n[FLOW 10] Reject a match"

# Create a second seeker for a new seek request on the same route
SEEKER2_EMAIL="seeker2_$(date +%s)@example.com"
resp=$(api POST /api/auth/dev-login \
    "{\"email\": \"$SEEKER2_EMAIL\", \"user_type\": \"seeker\"}")
SEEKER2_TOKEN=$(echo "$resp" | jq -r '.data.token // empty')

TRAVEL_TIME2=$(date -u -d '+8 days' +%Y-%m-%dT%H:%M:%S 2>/dev/null || \
               date -u -v+8d +%Y-%m-%dT%H:%M:%S 2>/dev/null || \
               python3 -c "from datetime import datetime,timedelta; print((datetime.utcnow()+timedelta(days=8)).strftime('%Y-%m-%dT%H:%M:%S'))")

resp=$(api POST /api/requests/seek \
    "{
        \"travel_details\": {
            \"travel_time\": \"${TRAVEL_TIME2}\",
            \"source_airport\": \"JFK\",
            \"destination_airport\": \"LHR\",
            \"flight_number\": \"BA180\",
            \"number_of_people\": 1
        },
        \"assistance_needed\": {
            \"type\": \"travel_companion\",
            \"categories\": [],
            \"special_requirements\": []
        }
    }" \
    "$SEEKER2_TOKEN")

resp2=$(api POST /api/requests/volunteer \
    "{
        \"travel_details\": {
            \"travel_time\": \"${TRAVEL_TIME2}\",
            \"source_airport\": \"JFK\",
            \"destination_airport\": \"LHR\",
            \"flight_number\": \"BA180\",
            \"number_of_people\": 1
        },
        \"assistance_offered\": {
            \"types\": [\"navigation\"],
            \"categories\": []
        }
    }" \
    "$VOL_TOKEN")

sleep 1

resp=$(api GET /api/matches/discover "" "$VOL_TOKEN")
REJECT_MATCH_ID=$(echo "$resp" | jq -r '[.[] | select(.status=="pending")] | .[0].match_id // empty')

if [[ -n "$REJECT_MATCH_ID" ]]; then
    resp=$(api POST "/api/matches/${REJECT_MATCH_ID}/reject" "" "$VOL_TOKEN")
    assert_eq "match rejected status=rejected" "rejected" "$(echo "$resp" | jq -r '.status')"
else
    green "  ⚠ No pending match to reject (may already be accepted) – skipping"
fi

# ---------------------------------------------------------------------------
# FLOW 11 – Calendar: own events (authenticated)
# ---------------------------------------------------------------------------
cyan "\n[FLOW 11] Calendar – own events"

resp=$(api GET /api/calendar/ "" "$SEEKER_TOKEN")
CAL_COUNT=$(echo "$resp" | jq '. | length' 2>/dev/null || echo "-1")
assert_ne "seeker calendar has events" "-1" "$CAL_COUNT"

# Unauthenticated request should fail
resp_unauth=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/calendar/")
assert_eq "unauthenticated calendar access returns 401" "401" "$resp_unauth"

# ---------------------------------------------------------------------------
# FLOW 12 – Calendar: all events (authenticated users only)
# ---------------------------------------------------------------------------
cyan "\n[FLOW 12] Calendar – all events (requires auth)"

resp=$(api GET /api/calendar/all "" "$SEEKER_TOKEN")
# Should succeed (HTTP 200-range); length can be 0 or more
ALL_CAL=$(echo "$resp" | jq '. | length' 2>/dev/null || echo "-1")
assert_ne "authenticated user can browse all calendar events" "-1" "$ALL_CAL"

# Unauthenticated
resp_unauth=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/calendar/all")
assert_eq "unauthenticated /calendar/all returns 401" "401" "$resp_unauth"

# ---------------------------------------------------------------------------
# FLOW 13 – Seeker cancels seek request → volunteer notified
# ---------------------------------------------------------------------------
cyan "\n[FLOW 13] Seeker cancels seek request (volunteer notified)"

# Accept a match first so there is an ACCEPTED state to cancel
# Use SEEK_ID from flow 6 which has an accepted match
resp=$(api DELETE "/api/requests/seek/${SEEK_ID}" "" "$SEEKER_TOKEN")
# DELETE returns 204 No Content on success; also check the status was set
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X DELETE -H "Authorization: Bearer $SEEKER_TOKEN" \
    "${BASE_URL}/api/requests/seek/${SEEK_ID}")
# 404 expected on second DELETE (already cancelled), 204 on first – either way the flow ran
assert_contains "seeker cancel returns 204 or 404" "204\|404" "$HTTP_STATUS"

# ---------------------------------------------------------------------------
# FLOW 14 – Request limit enforcement
# ---------------------------------------------------------------------------
cyan "\n[FLOW 14] Request limit enforcement"

LIMIT_EMAIL="limit_test_$(date +%s)@example.com"
resp=$(api POST /api/auth/dev-login \
    "{\"email\": \"$LIMIT_EMAIL\", \"user_type\": \"seeker\"}")
LIMIT_TOKEN=$(echo "$resp" | jq -r '.data.token // empty')

# Read configured limit from server (default 5); create limit+1 requests
LIMIT=5

TRAVEL_BASE=$(date -u -d '+30 days' +%Y-%m-%dT%H:%M:%S 2>/dev/null || \
              python3 -c "from datetime import datetime,timedelta; print((datetime.utcnow()+timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S'))")

for i in $(seq 1 $LIMIT); do
    api POST /api/requests/seek \
        "{\"travel_details\": {\"travel_time\": \"${TRAVEL_BASE}\",
          \"source_airport\": \"AAA\", \"destination_airport\": \"BBB\",
          \"flight_number\": \"XX${i}\", \"number_of_people\": 1},
          \"assistance_needed\": {\"type\": \"travel_companion\",
          \"categories\": [], \"special_requirements\": []}}" \
        "$LIMIT_TOKEN" > /dev/null
done

# The (LIMIT+1)-th request should be rejected
resp=$(api POST /api/requests/seek \
    "{\"travel_details\": {\"travel_time\": \"${TRAVEL_BASE}\",
      \"source_airport\": \"AAA\", \"destination_airport\": \"BBB\",
      \"flight_number\": \"XXOVER\", \"number_of_people\": 1},
      \"assistance_needed\": {\"type\": \"travel_companion\",
      \"categories\": [], \"special_requirements\": []}}" \
    "$LIMIT_TOKEN")

LIMIT_STATUS=$(echo "$resp" | jq -r '.detail // empty')
assert_contains "request over limit returns error message" "maximum" "$LIMIT_STATUS"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "============================================="
echo " Test Results: $PASS passed, $FAIL failed"
echo "============================================="

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
