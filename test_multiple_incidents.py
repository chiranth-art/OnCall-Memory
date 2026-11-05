
import time

from memory import (
    save_incident,
    save_outcome,
    find_similar,
    learned_patterns,
    client
)


try:
    print("\n========== MULTIPLE INCIDENT TEST ==========\n")

    # SECOND INCIDENT
    incident = {
        "id": "INC-002",
        "date": "2026-09-15T14:30:00Z",
        "service": "authentication-service",
        "symptoms": (
            "Users unable to log in due to repeated "
            "authentication request failures"
        ),
        "root_cause": (
            "Redis cache server ran out of memory"
        ),
        "fix_worked": (
            "Increased Redis memory allocation and "
            "implemented cache expiration"
        ),
        "fixes_failed": [
            "Restarting authentication-service "
            "did not resolve the issue"
        ],
        "minutes_to_resolve": 40
    }

    # STEP 1: SAVE SECOND INCIDENT
    print("STEP 1: Saving second incident...\n")

    save_incident(incident)

    print("INC-002 saved successfully!")

    # STEP 2: SAVE OUTCOME
    print("\nSTEP 2: Saving resolution feedback...\n")

    save_outcome(
        "INC-002",
        "SUCCESS: Increasing Redis memory and "
        "implementing cache expiration resolved the issue."
    )

    print("Outcome saved successfully!")

    # Wait for memory processing
    print("\nWaiting for memory processing...")
    time.sleep(8)

    # STEP 3: RECALL SECOND INCIDENT
    print("\nSTEP 3: Recalling authentication incidents...\n")

    results = find_similar(
        "authentication-service login failures caused by Redis cache memory exhaustion"
    )

    for result in results:
        print("-", result)

    # STEP 4: REFLECTION
    print("\nSTEP 4: Learning from both incidents...\n")

    patterns = learned_patterns(
        "Compare INC-001 and INC-002. "
        "What were their root causes, successful fixes, "
        "and failed troubleshooting attempts?"
    )

    print(patterns)

    print("\n========== TEST COMPLETED ==========")

except Exception as error:
    print("\nERROR:", error)
    raise

finally:
    client.close()
    print("\nHindsight client closed successfully.")
