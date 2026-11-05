
"""
memory.py
OnCall Memory - Hindsight Cloud Integration

Hindsight memory operations:
    save_incident(incident)          -> Store an incident
    save_outcome(incident_id, outcome) -> Store resolution feedback
    find_similar(error_text)         -> Recall similar incidents
    learned_patterns(question)       -> Reflect on past incidents
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

# Secure HTTPS certificate configuration
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

# One shared client for all memory operations
client = Hindsight(**client_kwargs)


# ==================================================
# 3. RETRY FUNCTION
# ==================================================


def _retry(
    fn: Callable,
    attempts: int = 3,
    delay: float = 1.5
):
    """Retry an operation when a temporary error occurs."""

    if attempts < 1:
        raise ValueError("Attempts must be at least 1.")

    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            return fn()

        except Exception as error:
            last_error = error

            if attempt < attempts - 1:
                print(
                    f"Attempt {attempt + 1} failed. "
                    f"Retrying in {delay} seconds..."
                )
                time.sleep(delay)

    if last_error is not None:
        raise last_error

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

    content = f"""
Incident ID: {incident['id']}
Date: {incident['date']}
Service: {incident['service']}
Symptoms: {incident['symptoms']}
Root Cause: {incident['root_cause']}
Fix That Worked: {incident['fix_worked']}
Failed Fixes: {incident['fixes_failed']}
Minutes to Resolve: {incident['minutes_to_resolve']}
"""

    return _retry(
        lambda: client.retain(
            bank_id=BANK_ID,
            content=content
        )
    )


# ==================================================
# 5. SAVE RESOLUTION OUTCOME
# ==================================================

def save_outcome(incident_id: str, outcome: str):
    """Validate and store incident resolution feedback."""

    if not isinstance(incident_id, str) or not incident_id.strip():
        raise ValueError(
            "Incident ID must be a non-empty string."
        )

    if not isinstance(outcome, str) or not outcome.strip():
        raise ValueError(
            "Outcome must be a non-empty string."
        )

    content = f"""
Incident ID: {incident_id.strip()}
Resolution Outcome: {outcome.strip()}
"""

    return _retry(
        lambda: client.retain(
            bank_id=BANK_ID,
            content=content
        )
    )


# ==================================================
# 6. FIND SIMILAR INCIDENTS
# ==================================================

def find_similar(error_text: str, limit: int = 5):
    """Retrieve relevant past incidents from Hindsight."""

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

    return [
        result.text
        for result in results.results
    ][:limit]


# ==================================================
# 7. LEARN PATTERNS USING REFLECTION
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
# 8. CLOSE CLIENT
# ==================================================

def close_client():
    """Close the shared Hindsight client when the application exits."""

    client.close()


# ==================================================
# 9. CONNECTION AND MEMORY TEST
# ==================================================

if __name__ == "__main__":

    try:
        print("\n========== ONCALL MEMORY ==========\n")

        print("Hindsight URL:", BASE_URL)
        print("Bank ID:", BANK_ID)
        print("API Key Loaded:", bool(API_KEY))

        incident = {
            "id": "INC-001",
            "date": "2026-08-12T21:10:00Z",
            "service": "payment-service",
            "symptoms": (
                "Orders failing with database connection "
                "timeout after a traffic spike"
            ),
            "root_cause": (
                "Database connection pool exhausted "
                "(limit 50)"
            ),
            "fix_worked": (
                "Raised connection pool size from 50 to 200"
            ),
            "fixes_failed": [
                "Restarted payment-service "
                "(issue returned in 10 minutes)"
            ],
            "minutes_to_resolve": 25
        }

        # STEP 1: SAVE INCIDENT
        print("\nSTEP 1: Saving incident...\n")

        save_incident(incident)

        print("Incident saved successfully!")

        # STEP 2: WAIT FOR MEMORY PROCESSING
        print("\nWaiting for Hindsight to process memory...")

        time.sleep(8)

        # STEP 3: RECALL SIMILAR INCIDENTS
        print("\nSTEP 2: RECALLING SIMILAR INCIDENTS\n")

        memories = find_similar(
            "database connection timeout on payment service"
        )

        if memories:
            for memory in memories:
                print("-", memory)
        else:
            print("No similar incidents found.")

        # STEP 4: REFLECT ON PAST INCIDENTS
        print("\nSTEP 3: LEARNING FROM PAST INCIDENTS\n")

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
