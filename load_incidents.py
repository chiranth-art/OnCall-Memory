"""
load_incidents.py
Loads realistic past incidents (and a few outcome feedbacks) into the
Hindsight memory bank, using the functions in memory.py.

Run ONCE:        python3 load_incidents.py
Run again:       python3 load_incidents.py --force   (only if you really want to)

A marker file (.incidents_loaded) stops accidental re-loading, because every
load uses a little of your Hindsight credit and creates duplicate memories.

The data is fictional (a food-delivery company) but built to show learning:
  - some problems REPEAT (database pool, Redis memory, Elasticsearch disk)
  - some fixes FAIL before the real one works (restarts, scaling)
  - Friday deployments keep causing trouble
"""

import os
import sys

from memory import save_incident, save_outcome, close_client

MARKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".incidents_loaded")

INCIDENTS = [
    {
        "id": "INC-001",
        "date": "2026-06-04T21:10:00Z",
        "service": "payment-service",
        "symptoms": "Orders failing with 'database connection timeout' after a traffic spike during dinner rush",
        "root_cause": "Database connection pool exhausted (limit 50)",
        "fix_worked": "Raised connection pool size from 50 to 200",
        "fixes_failed": ["Restarted payment-service (issue returned within 10 minutes)"],
        "minutes_to_resolve": 25,
    },
    {
        "id": "INC-002",
        "date": "2026-06-19T14:30:00Z",
        "service": "auth-service",
        "symptoms": "Users unable to log in; repeated authentication request failures",
        "root_cause": "Redis cache server ran out of memory",
        "fix_worked": "Increased Redis memory allocation and added expiry (TTL) to session keys",
        "fixes_failed": ["Restarted auth-service (no effect)"],
        "minutes_to_resolve": 40,
    },
    {
        "id": "INC-003",
        "date": "2026-07-02T10:45:00Z",
        "service": "order-api",
        "symptoms": "p95 latency jumped to 8 seconds; pods repeatedly OOMKilled after release v2.14",
        "root_cause": "Memory leak in the image-resize cache introduced in v2.14",
        "fix_worked": "Rolled back to v2.13, then shipped a fix with cache eviction",
        "fixes_failed": ["Scaled order-api pods from 4 to 8 (pods still ran out of memory)"],
        "minutes_to_resolve": 55,
    },
    {
        "id": "INC-004",
        "date": "2026-07-11T08:05:00Z",
        "service": "checkout-web",
        "symptoms": "Customers see browser HTTPS warning 'certificate expired' at checkout",
        "root_cause": "TLS certificate expired because the auto-renewal cron job had been disabled",
        "fix_worked": "Renewed the certificate manually and re-enabled the renewal cron job",
        "fixes_failed": ["Purged the CDN cache (no effect)"],
        "minutes_to_resolve": 35,
    },
    {
        "id": "INC-005",
        "date": "2026-07-23T20:50:00Z",
        "service": "payment-service",
        "symptoms": "Orders failing with 'database connection timeout' again on a Thursday evening",
        "root_cause": "Connection pool exhausted by a long-running query missing a database index",
        "fix_worked": "Added the missing index and kept the connection pool at 200",
        "fixes_failed": [
            "Restarted payment-service (returned within 15 minutes)",
            "Raised pool size alone (only delayed the failure by about 2 hours)",
        ],
        "minutes_to_resolve": 45,
    },
    {
        "id": "INC-006",
        "date": "2026-08-01T16:20:00Z",
        "service": "notification-service",
        "symptoms": "Order confirmation emails delayed by 3 hours",
        "root_cause": "Kafka consumer lag after a partition rebalance left consumers idle",
        "fix_worked": "Scaled consumers to match the number of partitions",
        "fixes_failed": ["Restarted consumers (lag came back)"],
        "minutes_to_resolve": 30,
    },
    {
        "id": "INC-007",
        "date": "2026-08-08T11:00:00Z",
        "service": "search-service",
        "symptoms": "Elasticsearch cluster status red; restaurant search returning errors; disk usage at 95%",
        "root_cause": "No retention policy on log indices, so old indices filled the disk",
        "fix_worked": "Deleted old indices and set a 14-day retention policy",
        "fixes_failed": ["Added a replica node (disk pressure continued)"],
        "minutes_to_resolve": 50,
    },
    {
        "id": "INC-008",
        "date": "2026-08-14T19:40:00Z",
        "service": "payment-service",
        "symptoms": "Payment failures began right after a Friday evening deployment of v5.3",
        "root_cause": "New fraud-check API call timed out under load",
        "fix_worked": "Rolled back the deployment to v5.2",
        "fixes_failed": ["Increased the fraud-check timeout (failures continued)"],
        "minutes_to_resolve": 20,
    },
    {
        "id": "INC-009",
        "date": "2026-08-27T13:15:00Z",
        "service": "order-api",
        "symptoms": "Load balancer returning 502 errors for all order requests",
        "root_cause": "Health-check path was changed in the latest release, so pods were marked unhealthy",
        "fix_worked": "Reverted the health-check path configuration",
        "fixes_failed": ["Restarted pods (still marked unhealthy)"],
        "minutes_to_resolve": 15,
    },
    {
        "id": "INC-010",
        "date": "2026-09-05T09:30:00Z",
        "service": "auth-service",
        "symptoms": "Login failures again; Redis memory usage very high",
        "root_cause": "New feature wrote Redis keys without an expiry (TTL)",
        "fix_worked": "Set a TTL on the new keys and flushed stale sessions",
        "fixes_failed": [
            "Restarted auth-service (no effect)",
            "Increased Redis memory only (problem returned in a day)",
        ],
        "minutes_to_resolve": 35,
    },
    {
        "id": "INC-011",
        "date": "2026-09-12T17:25:00Z",
        "service": "inventory-service",
        "symptoms": "Stock counts wrong; items showing negative quantity",
        "root_cause": "Messages processed twice after a retry configuration change",
        "fix_worked": "Made the message handler idempotent using unique message IDs",
        "fixes_failed": ["Manually corrected database counts (errors recurred the next day)"],
        "minutes_to_resolve": 90,
    },
    {
        "id": "INC-012",
        "date": "2026-09-20T12:10:00Z",
        "service": "checkout-web",
        "symptoms": "Checkout page taking 12 seconds to load",
        "root_cause": "Third-party payment SDK CDN outage blocked page rendering",
        "fix_worked": "Loaded the SDK asynchronously with a fallback source",
        "fixes_failed": ["Scaled up web servers (no effect, problem was external)"],
        "minutes_to_resolve": 25,
    },
    {
        "id": "INC-013",
        "date": "2026-09-25T21:05:00Z",
        "service": "payment-service",
        "symptoms": "Orders failing with 'database connection timeout' on a Friday night, third time this quarter",
        "root_cause": "Connection leak in the refund handler kept connections open, exhausting the pool",
        "fix_worked": "Fixed the leak by closing connections in a finally block, and kept pool size at 200",
        "fixes_failed": [
            "Restarted payment-service (returned within 20 minutes)",
            "Raised pool size alone (did not stop the leak)",
        ],
        "minutes_to_resolve": 38,
    },
    {
        "id": "INC-014",
        "date": "2026-10-07T15:45:00Z",
        "service": "api-gateway",
        "symptoms": "Mobile app users getting HTTP 429 'too many requests' errors",
        "root_cause": "Rate-limit configuration pushed that morning was far too strict",
        "fix_worked": "Reverted the rate limit to 1000 requests per minute",
        "fixes_failed": ["Restarted the gateway (config was reapplied)"],
        "minutes_to_resolve": 12,
    },
    {
        "id": "INC-015",
        "date": "2026-10-16T22:35:00Z",
        "service": "order-api",
        "symptoms": "Intermittent DNS resolution failures between services",
        "root_cause": "CoreDNS pods overloaded by high lookup volume",
        "fix_worked": "Scaled CoreDNS replicas and enabled node-local DNS caching",
        "fixes_failed": ["Restarted order-api (failures continued)"],
        "minutes_to_resolve": 60,
    },
    {
        "id": "INC-016",
        "date": "2026-10-24T10:20:00Z",
        "service": "search-service",
        "symptoms": "Elasticsearch disk usage at 92% again",
        "root_cause": "The retention-policy cleanup job had been failing silently",
        "fix_worked": "Fixed the cleanup job and added an alert at 80% disk usage",
        "fixes_failed": ["Deleted indices manually (disk filled again within a week)"],
        "minutes_to_resolve": 28,
    },
]

# Feedback entries: these teach the memory what works and what does not.
OUTCOMES = [
    ("INC-001", "Raising the connection pool to 200 resolved the timeouts for payment-service", True),
    ("INC-005", "Raising the pool size alone did not hold; adding the missing index fixed it", False),
    ("INC-010", "Setting a TTL on Redis keys stopped memory growth; adding memory alone did not", True),
    ("INC-013", "Restarting payment-service did not fix the timeouts; closing leaked connections did", False),
]


INCIDENT_DATES = {incident["id"]: incident["date"] for incident in INCIDENTS}


def main():
    force = "--force" in sys.argv

    if os.path.exists(MARKER) and not force:
        print("Incidents were already loaded (marker file found).")
        print("Use 'python3 load_incidents.py --force' only if you want to load them again.")
        return

    saved, failed = 0, 0

    print(f"\nLoading {len(INCIDENTS)} incidents...\n")
    for incident in INCIDENTS:
        try:
            save_incident(incident)
            saved += 1
            print(f"  saved {incident['id']}  ({incident['service']})")
        except Exception as error:  # keep going so one failure does not stop the rest
            failed += 1
            print(f"  FAILED {incident['id']}: {error}")

    print(f"\nLoading {len(OUTCOMES)} outcome feedback entries...\n")
    for incident_id, outcome, worked in OUTCOMES:
        try:
            save_outcome(incident_id, outcome, worked=worked, date=INCIDENT_DATES[incident_id])
            saved += 1
            print(f"  saved outcome for {incident_id}")
        except Exception as error:
            failed += 1
            print(f"  FAILED outcome for {incident_id}: {error}")

    print(f"\nDone. Saved: {saved}, failed: {failed}.")

    if failed == 0:
        with open(MARKER, "w") as marker_file:
            marker_file.write("loaded")
        print("Marker file created so this will not run twice by accident.")
    else:
        print("Some items failed, so no marker file was created. Fix the errors and run again.")

    print("\nHindsight processes memories in the background.")
    print("Wait a minute or two, then check the Memories page in Hindsight Cloud.")


if __name__ == "__main__":
    try:
        main()
    finally:
        close_client()