
"""
memory.py
OnCall Memory - Hindsight Cloud Integration

Hindsight memory operations:
    save_incident(incident)                    -> Store a past incident
    save_outcome(incident_id, outcome, worked) -> Store fix feedback
    find_similar(error_text, limit)            -> Recall relevant memories
    learned_patterns(question)                  -> Reflect on past incidents
    close_client()                             -> Close shared client

Improvements:
    1. Safe retry handling.
    2. Input validation before Hindsight API calls.
    3. Exact duplicate memory removal.
    4. Original incident details preserved.
    5. Existing public function interfaces maintained.
"""

import os
import time
from typing import Any, Callable

import certifi
from dotenv import load_dotenv
from hindsight_client import Hindsight


# ==================================================
# 1. ENVIRONMENT CONFIGURATION
# ==================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(
    dotenv_path=os.path.join(BASE_DIR, ".env"),
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

if not API_KEY:
    raise ValueError(
        "HINDSIGHT_API_KEY is missing. Check your .env file."
    )


# ==================================================
# 2. HINDSIGHT CLIENT
# ==================================================

client_kwargs: dict[str, Any] = {
    "base_url": BASE_URL,
    "api_key": API_KEY
}

client = Hindsight(**client_kwargs)


# ==================================================
# 3. RETRY FUNCTION
# ==================================================

def _retry(
    fn: Callable[[], Any],
    attempts: int = 3,
    delay: float = 1.5
) -> Any:
    """Retry an operation when a temporary error occurs."""

    if (
        not isinstance(attempts, int)
        or isinstance(attempts, bool)
        or attempts < 1
    ):
        raise ValueError("Attempts must be a positive integer.")

    if (
        not isinstance(delay, (int, float))
        or isinstance(delay, bool)
        or delay < 0
    ):
        raise ValueError("Delay must be a non-negative number.")

    for attempt in range(attempts):
        try:
            return fn()

        except Exception:
            if attempt == attempts - 1:
                raise

            wait_time = delay * (attempt + 1)

            print(
                f"Attempt {attempt + 1} failed. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)

    raise RuntimeError("Operation failed without an exception.")


# ==================================================
# 4. SAVE INCIDENT
# ==================================================

def save_incident(incident: dict):
    """Validate and store an incident in Hindsight."""

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
            f"Missing incident fields: {', '.join(missing_fields)}"
        )

    # Validate important text fields.
    text_fields = [
        "id",
        "date",
        "service",
        "symptoms",
        "root_cause",
        "fix_worked"
    ]

    for field in text_fields:
        if (
            not isinstance(incident[field], str)
            or not incident[field].strip()
        ):
            raise ValueError(
                f"Incident field '{field}' must be a non-empty string."
            )

    # Validate failed fixes.
    failed = incident["fixes_failed"]

    if isinstance(failed, (list, tuple)):
        failed_text = "; ".join(
            str(item) for item in failed if str(item).strip()
        ) or "none recorded"

    elif isinstance(failed, str):
        failed_text = failed.strip() or "none recorded"

    else:
        raise TypeError(
            "fixes_failed must be a string, list, or tuple."
        )

    content = f"""
Incident ID: {incident['id']}
Date: {incident['date']}
Service: {incident['service']}
Symptoms: {incident['symptoms']}
Root Cause: {incident['root_cause']}
Fix That Worked: {incident['fix_worked']}
Failed Fixes: {failed_text}
Minutes to Resolve: {incident['minutes_to_resolve']}
"""

    return _retry(
        lambda: client.retain(
            bank_id=BANK_ID,
            content=content,
            timestamp=incident["date"],
            context="incident post-mortem"
        )
    )


# ==================================================
# 5. SAVE RESOLUTION OUTCOME
# ==================================================

def save_outcome(
    incident_id: str,
    outcome: str,
    worked: bool | None = None,
    date: str | None = None
):
    """Validate and store incident resolution feedback.

    worked:
        True  -> fix worked
        False -> fix did not work
        None  -> result not specified

    date:
        Optional original incident date.
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

    if date is not None:
        if not isinstance(date, str) or not date.strip():
            raise ValueError(
                "date must be a non-empty string or None."
            )

    if worked is None:
        status_line = "Result: not specified\n"

    elif worked:
        status_line = "Result: the fix WORKED\n"

    else:
        status_line = "Result: the fix did NOT work\n"

    content = f"""
Incident ID: {incident_id.strip()}
{status_line}Resolution Outcome: {outcome.strip()}
"""

    return _retry(
        lambda: client.retain(
            bank_id=BANK_ID,
            content=content,
            timestamp=date,
            context="fix outcome feedback"
        )
    )


# ==================================================
# 6. MEMORY DEDUPLICATION
# ==================================================

def _normalize_memory(text: str) -> str:
    """
    Normalize memory text for exact duplicate detection.

    Case and repeated whitespace are ignored.
    Original memory text is preserved in the returned results.

    This does not merge different facts or different fixes.
    """

    return " ".join(text.casefold().split())


def _deduplicate_memories(memories: list[str]) -> list[str]:
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
# 7. FIND SIMILAR INCIDENTS
# ==================================================

def find_similar(error_text: str, limit: int = 5):
    """
    Retrieve relevant memories from Hindsight.

    Exact duplicate memories are removed before returning results.

    Different memories from the same incident are preserved because
    they may contain separate root causes, successful fixes, or
    failed troubleshooting attempts.
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

    results = _retry(
        lambda: client.recall(
            bank_id=BANK_ID,
            query=error_text.strip()
        )
    )

    raw_memories = [
        result.text
        for result in results.results
        if getattr(result, "text", None)
    ]

    unique_memories = _deduplicate_memories(raw_memories)

    return unique_memories[:limit]


# ==================================================
# 8. LEARN PATTERNS USING REFLECTION
# ==================================================

def learned_patterns(question: str):
    """Use Hindsight reflection to identify learned patterns."""

    if not isinstance(question, str) or not question.strip():
        raise ValueError(
            "Reflection question must be a non-empty string."
        )

    answer = _retry(
        lambda: client.reflect(
            bank_id=BANK_ID,
            query=question.strip()
        )
    )

    return getattr(answer, "text", None) or str(answer)


# ==================================================
# 9. CLOSE CLIENT
# ==================================================

def close_client():
    """Close the shared Hindsight client."""

    client.close()


# ==================================================
# 10. SAFE DIRECT TEST
# ==================================================

if __name__ == "__main__":

    try:
        print("\n========== ONCALL MEMORY ==========\n")

        print("Hindsight URL:", BASE_URL)
        print("Bank ID:", BANK_ID)
        print("API Key Loaded:", bool(API_KEY))

        # This test only retrieves existing memories.
        # It does NOT save another incident.

        print("\nSTEP 1: RECALLING SIMILAR INCIDENTS\n")

        memories = find_similar(
            "database connection timeout on payment service",
            limit=5
        )

        if memories:
            for index, memory in enumerate(memories, start=1):
                print(f"\nMEMORY {index}")
                print("-" * 50)
                print(memory)
        else:
            print("No similar incidents found.")

        print("\nSTEP 2: LEARNING FROM PAST INCIDENTS\n")

        patterns = learned_patterns(
            "What fixed database connection timeouts before?"
        )

        print(patterns)

        print("\n========== TEST COMPLETED ==========")

    except Exception as error:
        print("\nERROR:", error)
        raise

    finally:
        close_client()
        print("\nHindsight client closed successfully.")
