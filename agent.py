import os
import json
import re

from llm import generate_ai_analysis


def load_all_incidents():
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "sample_incidents.json"
    )

    if not os.path.exists(file_path):
        raise FileNotFoundError("sample_incidents.json not found.")

    with open(file_path, "r", encoding="utf-8") as file:
        incidents = json.load(file)

    if not isinstance(incidents, list):
        raise ValueError("Incident database must be a list.")

    return incidents


def find_local_incidents(error_text, limit=5):

    if not isinstance(error_text, str) or not error_text.strip():
        return []

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
        word for word in re.findall(r"\b\w+\b", error_text.lower())
        if len(word) > 3 and word not in stop_words
    }

    matches = []

    for incident in incidents:

        if not isinstance(incident, dict):
            continue

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

    matches.sort(key=lambda item: item[0], reverse=True)

    return [
        incident for score, incident in matches[:limit]
    ]


def respond_to_incident(error_text):

    if not isinstance(error_text, str) or not error_text.strip():
        raise ValueError("Error description cannot be empty.")

    print("\nIncident received!")
    print("Searching local historical incidents...")

    historical_incidents = find_local_incidents(error_text)

    # If no keyword matches are found, use the available
    # records for comparison instead of stopping the analysis.
    if not historical_incidents:
        print("No direct matches found. Loading available records...")
        historical_incidents = load_all_incidents()

    print(f"Historical incidents found: {len(historical_incidents)}")
    print("\nGenerating AI incident analysis...\n")

    result = generate_ai_analysis(
        error_text,
        historical_incidents
    )

    return result


if __name__ == "__main__":

    test_incident = (
        "Database connection timeout in payment-service. "
        "Customer orders are failing."
    )

    print(respond_to_incident(test_incident))