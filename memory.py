"""
OnCall Memory - Hindsight Cloud with Local Fallback

Functions:
    save_incident()
    save_outcome()
    find_similar()
    learned_patterns()
    close_client()
"""

import os
import json

import certifi
from dotenv import load_dotenv

try:
    from hindsight_client import Hindsight
except ImportError:
    Hindsight = None


# ==================================================
# 1. CONFIGURATION
# ==================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(
    os.path.join(BASE_DIR, ".env"),
    override=True
)

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "oncall-memory")

BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL",
    "https://api.hindsight.vectorize.io"
)

API_KEY = os.getenv("HINDSIGHT_API_KEY")

LOCAL_MEMORY_FILE = os.path.join(
    BASE_DIR, "local_memory.json"
)

INCIDENT_FILE = os.path.join(
    BASE_DIR, "sample_incidents.json"
)


# ==================================================
# 2. INITIALIZE HINDSIGHT
# ==================================================

client = None
hindsight_available = False


def initialize_client():

    global client, hindsight_available

    if not API_KEY:
        print("Hindsight API key missing.")
        print("Using local memory.")
        return

    if Hindsight is None:
        print("Hindsight package not installed.")
        print("Using local memory.")
        return

    try:
        client = Hindsight(
            base_url=BASE_URL,
            api_key=API_KEY
        )

        hindsight_available = True

        print("Hindsight client initialized.")

    except Exception as error:

        client = None
        hindsight_available = False

        print("Hindsight initialization failed:", error)
        print("Using local memory.")


initialize_client()


# ==================================================
# 3. LOCAL MEMORY FUNCTIONS
# ==================================================

def load_local_memory():

    if not os.path.exists(LOCAL_MEMORY_FILE):
        return []

    try:
        with open(
            LOCAL_MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return data

        print("Invalid local memory format.")
        return []

    except (OSError, json.JSONDecodeError) as error:

        print("Local memory loading error:", error)
        return []


def save_local_memory(records):

    with open(
        LOCAL_MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(records, file, indent=4)


def load_historical_incidents():

    try:
        with open(
            INCIDENT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return data

        print("Historical incident database is invalid.")
        return []

    except (OSError, json.JSONDecodeError) as error:

        print("Historical database error:", error)
        return []


def disable_hindsight(error):

    global client, hindsight_available

    print("\nHindsight API unavailable:", error)
    print("Switching to local memory.")

    try:
        if client is not None:
            client.close()
    except Exception:
        pass

    client = None
    hindsight_available = False


# ==================================================
# 4. SAVE INCIDENT
# ==================================================

def save_incident(incident):

    if not isinstance(incident, dict):
        raise TypeError(
            "Incident must be provided as a dictionary."
        )

    required_fields = [
        "id",
        "date",
        "service",
        "symptoms",
        "root_cause",
        "fix_worked",
        "fixes_failed",
        "minutes_to_resolve"
    ]

    missing_fields = [
        field for field in required_fields
        if field not in incident
    ]

    if missing_fields:
        raise ValueError(
            "Missing incident fields: "
            + ", ".join(missing_fields)
        )

    failed_fixes = incident["fixes_failed"]

    if isinstance(failed_fixes, (list, tuple)):
        failed_fixes = "; ".join(
            str(item) for item in failed_fixes
        )

    content = f"""
Incident ID: {incident['id']}
Date: {incident['date']}
Service: {incident['service']}
Symptoms: {incident['symptoms']}
Root Cause: {incident['root_cause']}
Fix That Worked: {incident['fix_worked']}
Failed Fixes: {failed_fixes}
Minutes to Resolve: {incident['minutes_to_resolve']}
"""

    if hindsight_available:

        try:
            return client.retain(
                bank_id=BANK_ID,
                content=content,
                timestamp=incident["date"],
                context="incident post-mortem"
            )

        except Exception as error:
            disable_hindsight(error)

    records = load_local_memory()

    # Update an existing local incident instead of duplicating it.
    records = [
        record for record in records
        if not (
            record.get("type") == "incident"
            and record.get("data", {}).get("id") == incident["id"]
        )
    ]

    records.append({
        "type": "incident",
        "data": incident
    })

    save_local_memory(records)

    print("Incident saved in local memory.")

    return True


# ==================================================
# 5. SAVE RESOLUTION OUTCOME
# ==================================================

def save_outcome(
    incident_id,
    outcome,
    worked=None
):

    if not isinstance(incident_id, str) or not incident_id.strip():
        raise ValueError(
            "Incident ID must be a non-empty string."
        )

    if not isinstance(outcome, str) or not outcome.strip():
        raise ValueError(
            "Outcome must be a non-empty string."
        )

    if worked is not None and not isinstance(worked, bool):
        raise TypeError(
            "worked must be True, False, or None."
        )

    content = f"""
Incident ID: {incident_id}
Outcome: {outcome}
Fix worked: {worked}
"""

    if hindsight_available:

        try:
            return client.retain(
                bank_id=BANK_ID,
                content=content,
                context="fix outcome feedback"
            )

        except Exception as error:
            disable_hindsight(error)

    records = load_local_memory()

    records.append({
        "type": "outcome",
        "incident_id": incident_id.strip(),
        "outcome": outcome.strip(),
        "worked": worked
    })

    save_local_memory(records)

    print("Outcome saved in local memory.")

    return True


# ==================================================
# 6. FIND SIMILAR INCIDENTS
# ==================================================

def find_similar(error_text, limit=5):

    if not isinstance(error_text, str) or not error_text.strip():
        raise ValueError(
            "Error description must be a non-empty string."
        )

    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or limit < 1
    ):
        raise ValueError(
            "Limit must be a positive integer."
        )

    if hindsight_available:

        try:
            results = client.recall(
                bank_id=BANK_ID,
                query=error_text.strip()
            )

            return [
                result.text
                for result in results.results
            ][:limit]

        except Exception as error:
            disable_hindsight(error)

    # LOCAL FALLBACK

    historical = load_historical_incidents()
    local_records = load_local_memory()

    local_incidents = [
        record["data"]
        for record in local_records
        if (
            isinstance(record, dict)
            and record.get("type") == "incident"
            and isinstance(record.get("data"), dict)
        )
    ]

    incidents = historical + local_incidents

    query_words = set(error_text.lower().split())

    scored = []

    for incident in incidents:

        if not isinstance(incident, dict):
            continue

        searchable = " ".join(
            str(value)
            for value in incident.values()
        ).lower()

        incident_words = set(searchable.split())

        score = len(query_words.intersection(incident_words))

        if score > 0:
            scored.append((score, incident))

    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        json.dumps(incident, indent=4)
        for score, incident in scored[:limit]
    ]


# ==================================================
# 7. LEARN PATTERNS
# ==================================================

def learned_patterns(question):

    if not isinstance(question, str) or not question.strip():
        raise ValueError(
            "Reflection question must be a non-empty string."
        )

    if hindsight_available:

        try:
            answer = client.reflect(
                bank_id=BANK_ID,
                query=question.strip()
            )

            return (
                getattr(answer, "text", None)
                or str(answer)
            )

        except Exception as error:
            disable_hindsight(error)

    # LOCAL PATTERN LEARNING

    incidents = load_historical_incidents()

    local_records = load_local_memory()

    local_incidents = [
        record["data"]
        for record in local_records
        if (
            isinstance(record, dict)
            and record.get("type") == "incident"
            and isinstance(record.get("data"), dict)
        )
    ]

    incidents.extend(local_incidents)

    if not incidents:
        return "No historical incidents are available."

    patterns = []

    for incident in incidents:

        patterns.append(
            f"""
Incident: {incident.get('id', 'Unknown')}
Service: {incident.get('service', 'Unknown')}
Root Cause: {incident.get('root_cause', 'Not recorded')}
Successful Fix: {incident.get('fix_worked', 'Not recorded')}
Failed Fixes: {incident.get('fixes_failed', 'Not recorded')}
"""
        )

    return "\n".join(patterns)


# ==================================================
# 8. CLOSE CLIENT
# ==================================================

def close_client():

    global client, hindsight_available

    if client is not None:

        try:
            client.close()

        except Exception as error:
            print("Client closing error:", error)

    client = None
    hindsight_available = False


# ==================================================
# 9. TEST
# ==================================================

if __name__ == "__main__":

    try:

        print("\n========== ONCALL MEMORY ==========\n")

        print(
            "Memory mode:",
            "Hindsight" if hindsight_available else "Local"
        )

        incident = {
            "id": "TEST-001",
            "date": "2026-11-06T10:00:00Z",
            "service": "payment-service",
            "symptoms": "Database connection timeout",
            "root_cause": "Database connection pool exhausted",
            "fix_worked": "Increased connection pool size",
            "fixes_failed": ["Restarting the service"],
            "minutes_to_resolve": 25
        }

        print("\nSTEP 1: Saving incident...")

        save_incident(incident)

        print("\nSTEP 2: Finding similar incidents...")

        memories = find_similar(
            "database connection timeout"
        )

        if memories:
            for memory in memories:
                print("\n", memory)
        else:
            print("No similar incidents found.")

        print("\nSTEP 3: Learning patterns...")

        patterns = learned_patterns(
            "What fixed database connection timeouts?"
        )

        print(patterns)

        print("\n========== TEST COMPLETED ==========")

    except Exception as error:

        print("\nTEST ERROR:", error)

    finally:

        close_client()

        print("\nMemory client closed.")