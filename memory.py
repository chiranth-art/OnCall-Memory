
"""
memory.py
OnCall Memory - Hindsight Cloud with Local Fallback

Responsibilities:
1. Save historical production incidents.
2. Save successful and failed resolution outcomes.
3. Recall similar incidents from Hindsight.
4. Learn patterns from historical incidents.
5. Retry temporary Hindsight failures.
6. Fall back to local JSON memory when Hindsight is unavailable.
"""

import os
import json
import time
import certifi

from typing import Any
from dotenv import load_dotenv


# ==================================================
# 1. HINDSIGHT SDK IMPORT
# ==================================================

Hindsight: Any = None

try:
    from hindsight_client import Hindsight as HindsightClient
    Hindsight = HindsightClient
except ImportError:
    print("Hindsight package not installed.")
    print("Local memory will be used.")


# ==================================================
# 2. CONFIGURATION
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
# 3. RETRY HANDLING
# ==================================================

def _retry(operation, attempts=3, delay=1.5):
    """
    Retry an operation when it fails.

    Default behaviour:
        Attempt 1 -> immediate
        Attempt 2 -> wait 1.5 seconds
        Attempt 3 -> wait 3 seconds

    Raises the final exception if every attempt fails.
    """

    if (
        not isinstance(attempts, int)
        or isinstance(attempts, bool)
        or attempts < 1
    ):
        raise ValueError(
            "Retry attempts must be a positive integer."
        )

    if (
        not isinstance(delay, (int, float))
        or isinstance(delay, bool)
        or delay < 0
    ):
        raise ValueError(
            "Retry delay must be a non-negative number."
        )

    for attempt in range(attempts):

        try:
            return operation()

        except Exception:

            if attempt == attempts - 1:
                raise

            wait_time = delay * (attempt + 1)

            print(
                f"Attempt {attempt + 1} failed. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)


# ==================================================
# 4. INITIALIZE HINDSIGHT
# ==================================================

client: Any = None
hindsight_available = False


def initialize_client():
    """Initialize the Hindsight cloud client."""

    global client, hindsight_available

    if not API_KEY:
        print("Hindsight API key missing.")
        print("Using local memory.")
        return

    if Hindsight is None:
        print("Hindsight SDK unavailable.")
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


# ==================================================
# 5. LOCAL MEMORY FUNCTIONS
# ==================================================

def load_local_memory():
    """Load records from local JSON memory."""

    if not os.path.exists(LOCAL_MEMORY_FILE):
        return []

    try:
        with open(
            LOCAL_MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            records = json.load(file)

        if isinstance(records, list):
            return records

        print("Invalid local memory format.")
        return []

    except (OSError, json.JSONDecodeError) as error:
        print("Could not load local memory:", error)
        return []


def save_local_memory(records):
    """Save records to local JSON memory."""

    if not isinstance(records, list):
        raise TypeError("Local memory records must be a list.")

    with open(
        LOCAL_MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            indent=4,
            ensure_ascii=False
        )


def load_historical_incidents():
    """Load historical incidents from sample_incidents.json."""

    if not os.path.exists(INCIDENT_FILE):
        return []

    try:
        with open(
            INCIDENT_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            incidents = json.load(file)

        if not isinstance(incidents, list):
            print("Historical incident file must contain a list.")
            return []

        return incidents

    except (OSError, json.JSONDecodeError) as error:
        print("Could not load historical incidents:", error)
        return []


# ==================================================
# 6. DISABLE HINDSIGHT SAFELY
# ==================================================

def disable_hindsight(error):
    """Disable Hindsight and switch to local memory."""

    global client, hindsight_available

    print("Hindsight operation failed:", error)
    print("Switching to local memory.")

    if client is not None:

        try:
            client.close()

        except Exception as close_error:
            print("Client closing error:", close_error)

    client = None
    hindsight_available = False


# ==================================================
# 7. MEMORY NORMALIZATION AND DEDUPLICATION
# ==================================================

def _normalize_memory(memory):
    """Normalize memory text for duplicate comparison."""

    if not isinstance(memory, str):
        return ""

    return " ".join(memory.lower().split())


def _deduplicate_memories(memories):
    """Remove exact duplicate memories while preserving order."""

    unique_memories = []
    seen = set()

    for memory in memories:

        if not isinstance(memory, str) or not memory.strip():
            continue

        normalized = _normalize_memory(memory)

        if normalized in seen:
            continue

        seen.add(normalized)
        unique_memories.append(memory.strip())

    return unique_memories


# ==================================================
# 8. SAVE INCIDENT
# ==================================================

def save_incident(incident):
    """
    Save a production incident to Hindsight.

    If Hindsight fails after retries, save it locally.
    """

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
        field
        for field in required_fields
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

    if hindsight_available and client is not None:

        try:
            return _retry(
                lambda: client.retain(
                    bank_id=BANK_ID,
                    content=content,
                    timestamp=incident["date"],
                    context="incident post-mortem"
                )
            )

        except Exception as error:
            disable_hindsight(error)

    # LOCAL FALLBACK

    records = load_local_memory()

    # Update an existing incident instead of duplicating it.
    records = [
        record
        for record in records
        if not (
            isinstance(record, dict)
            and record.get("type") == "incident"
            and isinstance(record.get("data"), dict)
            and record["data"].get("id") == incident["id"]
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
# 9. SAVE RESOLUTION OUTCOME
# ==================================================

def save_outcome(incident_id, outcome, worked=None):
    """
    Save feedback about an incident's resolution.

    worked:
        True  -> Fix worked.
        False -> Fix failed.
        None  -> Outcome not specified.
    """

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

    if hindsight_available and client is not None:

        try:
            return _retry(
                lambda: client.retain(
                    bank_id=BANK_ID,
                    content=content,
                    context="fix outcome feedback"
                )
            )

        except Exception as error:
            disable_hindsight(error)

    # LOCAL FALLBACK

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
# 10. FIND SIMILAR INCIDENTS
# ==================================================

def find_similar(error_text, limit=5):
    """
    Find incidents similar to the current production error.

    Uses Hindsight semantic recall when available.
    Otherwise uses local keyword-overlap matching.
    """

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

    if hindsight_available and client is not None:

        try:
            results = _retry(
                lambda: client.recall(
                    bank_id=BANK_ID,
                    query=error_text.strip()
                )
            )

            memories = []

            recalled_results = getattr(
                results,
                "results",
                []
            ) or []

            for result in recalled_results:

                memory_text = getattr(
                    result,
                    "text",
                    None
                )

                if (
                    isinstance(memory_text, str)
                    and memory_text.strip()
                ):
                    memories.append(memory_text)

            return _deduplicate_memories(memories)[:limit]

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

        score = len(
            query_words.intersection(incident_words)
        )

        if score > 0:
            scored.append((score, incident))

    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    memories = [
        json.dumps(incident, indent=4)
        for score, incident in scored[:limit]
    ]

    return _deduplicate_memories(memories)[:limit]


# ==================================================
# 11. LEARN PATTERNS
# ==================================================

def learned_patterns(question):
    """
    Learn patterns from previous incidents.

    Uses Hindsight reflection with active directives.
    Uses local incident data if Hindsight is unavailable.
    """

    if not isinstance(question, str) or not question.strip():
        raise ValueError(
            "Reflection question must be a non-empty string."
        )

    if hindsight_available and client is not None:

        try:
            answer = _retry(
                lambda: client.reflect(
                    bank_id=BANK_ID,
                    query=question.strip(),
                    apply_all_directives=True
                )
            )

            answer_text = getattr(
                answer,
                "text",
                None
            )

            return answer_text or str(answer)

        except Exception as error:
            disable_hindsight(error)

    # LOCAL FALLBACK

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
# 12. CLOSE CLIENT
# ==================================================

def close_client():
    """Safely close the Hindsight client."""

    global client, hindsight_available

    if client is not None:

        try:
            client.close()

        except Exception as error:
            print("Client closing error:", error)

    client = None
    hindsight_available = False


# ==================================================
# 13. INITIALIZE ON IMPORT
# ==================================================

initialize_client()
