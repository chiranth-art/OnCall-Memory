
"""
memory.py
OnCall Memory - Hindsight Cloud Integration

Functions:
    save_incident(incident)       -> Store an incident
    save_outcome(incident_id, outcome) -> Store resolution feedback
    find_similar(error_text)      -> Recall similar incidents
    learned_patterns(question)    -> Learn patterns from past incidents
"""

import os
import time
from typing import Any

import certifi
from dotenv import load_dotenv
from hindsight_client import Hindsight


# --------------------------------------------------
# 1. ENVIRONMENT CONFIGURATION
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(
    dotenv_path=os.path.join(BASE_DIR, ".env"),
    override=True
)

# Use certifi certificates for secure HTTPS connections
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

# Create Hindsight client
client_kwargs: dict[str, Any] = {
    "base_url": BASE_URL,
    "api_key": API_KEY
}

client = Hindsight(**client_kwargs)


# --------------------------------------------------
# 2. RETRY FUNCTION
# --------------------------------------------------

def _retry(fn, attempts=3, delay=1.5):
    """Retry an operation if a temporary error occurs."""

    last_error = None

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

    raise RuntimeError("Operation failed.")


# --------------------------------------------------
# 3. SAVE INCIDENT
# --------------------------------------------------

def save_incident(incident: dict):
    """Store an incident and its resolution details."""

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


# --------------------------------------------------
# 4. SAVE OUTCOME
# --------------------------------------------------

def save_outcome(incident_id: str, outcome: str):
    """Remember whether a resolution worked or failed."""

    content = f"""
Incident ID: {incident_id}
Resolution Outcome: {outcome}
"""

    return _retry(
        lambda: client.retain(
            bank_id=BANK_ID,
            content=content
        )
    )


# --------------------------------------------------
# 5. FIND SIMILAR INCIDENTS
# --------------------------------------------------

def find_similar(error_text: str, limit: int = 5):
    """Retrieve memories related to a new error."""

    results = _retry(
        lambda: client.recall(
            bank_id=BANK_ID,
            query=error_text
        )
    )

    return [
        result.text
        for result in results.results
    ][:limit]


# --------------------------------------------------
# 6. LEARN PATTERNS
# --------------------------------------------------

def learned_patterns(question: str):
    """Use Hindsight reflection to identify learned patterns."""

    answer = _retry(
        lambda: client.reflect(
            bank_id=BANK_ID,
            query=question
        )
    )

    return getattr(answer, "text", None) or str(answer)


# --------------------------------------------------
# 7. CONNECTION TEST
# --------------------------------------------------

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

        # Save
        print("\nSTEP 1: Saving incident...\n")

        save_incident(incident)

        print("Incident saved successfully!")

        # Wait for processing
        print("\nWaiting for Hindsight to process memory...")
        time.sleep(8)

        # Recall
        print("\nSTEP 2: RECALLING SIMILAR INCIDENTS\n")

        memories = find_similar(
            "database connection timeout on payment service"
        )

        if memories:
            for memory in memories:
                print("-", memory)
        else:
            print("No similar incidents found.")

        # Reflect
        print("\nSTEP 3: LEARNING FROM PAST INCIDENTS\n")

        patterns = learned_patterns(
            "What fixed database connection timeouts before?"
        )

        print(patterns)

        print("\n========== TEST COMPLETED ==========")

    except Exception as error:
        print(f"\nERROR: {error}")
        raise

    finally:
        client.close()
        print("\nHindsight client closed successfully.")
