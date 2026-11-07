
"""
agent.py
OnCall Incident Response Agent

Responsibilities:
1. Accept a production error.
2. Retrieve similar incidents from Hindsight.
3. Match recalled incident IDs to canonical incident records.
4. Use local keyword matching as a fallback.
5. Generate an evidence-based incident briefing using Groq.
"""

import re

from llm import generate_ai_analysis
import memory
from load_incidents import INCIDENTS


# ==================================================
# 1. CANONICAL HISTORICAL INCIDENTS
# ==================================================

def load_all_incidents():
    """Return the canonical historical incident records."""

    if not isinstance(INCIDENTS, list):
        raise ValueError("Historical incident database must be a list.")

    return [
        incident
        for incident in INCIDENTS
        if isinstance(incident, dict)
        and isinstance(incident.get("id"), str)
    ]


# ==================================================
# 2. EXTRACT INCIDENT IDS FROM HINDSIGHT
# ==================================================

def extract_incident_ids(memories):
    """Extract unique incident IDs from recalled memories."""

    if not isinstance(memories, list):
        return []

    incident_ids = []
    seen = set()

    for memory in memories:

        if not isinstance(memory, str):
            continue

        matches = re.findall(
            r"\bINC-\d+\b",
            memory,
            flags=re.IGNORECASE
        )

        for incident_id in matches:

            incident_id = incident_id.upper()

            if incident_id not in seen:
                seen.add(incident_id)
                incident_ids.append(incident_id)

    return incident_ids


# ==================================================
# 3. MATCH RECALLS TO CANONICAL INCIDENTS
# ==================================================

def match_historical_incidents(incident_ids):
    """Match recalled IDs to their exact structured records."""

    if not isinstance(incident_ids, list):
        raise TypeError("Incident IDs must be provided as a list.")

    canonical_incidents = load_all_incidents()

    incident_map = {
        incident["id"]: incident
        for incident in canonical_incidents
    }

    matched = []
    seen = set()

    for incident_id in incident_ids:

        if not isinstance(incident_id, str):
            continue

        incident_id = incident_id.upper()

        if incident_id in seen:
            continue

        incident = incident_map.get(incident_id)

        if incident is not None:
            matched.append(incident)
            seen.add(incident_id)

    return matched


# ==================================================
# 4. LOCAL KEYWORD FALLBACK
# ==================================================

def find_local_incidents(error_text, limit=5):
    """Find relevant incidents using local keyword matching."""

    if not isinstance(error_text, str) or not error_text.strip():
        return []

    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("Limit must be a positive integer.")

    incidents = load_all_incidents()

    stop_words = {
        "service", "failure", "error", "issue",
        "the", "in", "and", "is", "a", "of",
        "after", "because", "with", "due", "to",
        "are", "was", "were", "has", "have",
        "this", "that", "from", "for", "not",
        "when", "then", "been", "being"
    }

    keywords = {
        word
        for word in re.findall(r"\b\w+\b", error_text.lower())
        if len(word) > 3 and word not in stop_words
    }

    matches = []

    for incident in incidents:

        searchable_text = " ".join([
            str(incident.get("service", "")),
            str(incident.get("symptoms", "")),
            str(incident.get("root_cause", ""))
        ]).lower()

        searchable_words = set(
            re.findall(r"\b\w+\b", searchable_text)
        )

        score = len(keywords.intersection(searchable_words))

        if score > 0:
            matches.append((score, incident))

    matches.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        incident
        for score, incident in matches[:limit]
    ]


# ==================================================
# 5. HINDSIGHT RETRIEVAL
# ==================================================


def retrieve_historical_incidents(error_text, limit=5):
    """
    Retrieve relevant incidents through Hindsight.

    Falls back to canonical local keyword matching if
    Hindsight is unavailable or retrieval fails.
    """

    if memory.hindsight_available:

        print("\nSearching Hindsight memory...")

        try:
            recalled_memories = memory.find_similar(
                error_text,
                limit=limit
            )

            # Check again because find_similar may have
            # disabled Hindsight after a retrieval failure.
            if memory.hindsight_available:

                incident_ids = extract_incident_ids(
                    recalled_memories
                )

                historical_incidents = match_historical_incidents(
                    incident_ids
                )

                if historical_incidents:
                    print(
                        f"Hindsight recalled "
                        f"{len(historical_incidents)} structured incidents."
                    )

                    print(
                        "Recalled incident IDs:",
                        ", ".join(
                            incident["id"]
                            for incident in historical_incidents
                        )
                    )

                    return historical_incidents, "Hindsight"

                print(
                    "No usable incident IDs found in Hindsight results."
                )

            else:
                print(
                    "Hindsight became unavailable during retrieval."
                )

        except Exception as error:
            print("Hindsight retrieval failed:", error)

    else:
        print("\nHindsight unavailable. Using local memory.")

    print("Searching canonical local incident records...")

    historical_incidents = find_local_incidents(
        error_text,
        limit=limit
    )

    return historical_incidents, "Local fallback"



# ==================================================
# 6. MAIN INCIDENT RESPONSE
# ==================================================

def respond_to_incident(error_text):

    if not isinstance(error_text, str) or not error_text.strip():
        raise ValueError("Error description cannot be empty.")

    print("\n========================================")
    print("       ONCALL INCIDENT RESPONSE")
    print("========================================")

    print("\nIncident received!")

    historical_incidents, retrieval_source = (
        retrieve_historical_incidents(error_text)
    )

    print("\nRetrieval source:", retrieval_source)

    if not historical_incidents:

        print("No relevant historical incidents found.")

        return (
            "No relevant historical incidents were found. "
            "Please investigate the current incident using "
            "available logs, metrics and monitoring evidence."
        )

    print(
        "Historical incidents selected:",
        len(historical_incidents)
    )

    print("\nGenerating AI incident analysis...\n")

    result = generate_ai_analysis(
        error_text,
        historical_incidents
    )

    return result


# ==================================================
# 7. RUN AGENT
# ==================================================

if __name__ == "__main__":

    test_incident = (
        "Database connection timeout in payment-service. "
        "Customer orders are failing."
    )

    try:

        print(respond_to_incident(test_incident))

    finally:

        memory.close_client()

