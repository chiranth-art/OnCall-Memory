"""
OnCall Incident Response Agent
Local Incident Search + Groq AI + Function Calling
"""

import json
import os
import re

from llm import generate_ai_analysis


# ==================================================
# 1. LOAD AND SEARCH LOCAL INCIDENTS
# ==================================================

def find_local_incidents(error_text, limit=5):

    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "sample_incidents.json"
    )

    with open(file_path, "r", encoding="utf-8") as file:
        incidents = json.load(file)

    if not isinstance(incidents, list):
        raise ValueError("Incident database must be a list.")

    stop_words = {
        "service", "failure", "error", "issue",
        "the", "in", "and", "is", "a", "of",
        "after", "because", "with", "due", "to",
        "are", "was", "were", "has", "have"
    }

    keywords = {
        word for word in re.findall(
            r"\b\w+\b", error_text.lower()
        )
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


# ==================================================
# 2. LEARN FROM HISTORICAL INCIDENTS
# ==================================================

def learn_local_patterns(incidents):

    if not incidents:
        return "No historical patterns available."

    patterns = []

    patterns.append("ROOT CAUSES:")

    for incident in incidents:
        patterns.append(
            "- " + str(
                incident.get("root_cause", "Not recorded")
            )
        )

    patterns.append("\nSUCCESSFUL FIXES:")

    for incident in incidents:
        patterns.append(
            "- " + str(
                incident.get("fix_worked", "Not recorded")
            )
        )

    patterns.append("\nFAILED FIXES:")

    for incident in incidents:
        patterns.append(
            "- " + str(
                incident.get("fixes_failed", "Not recorded")
            )
        )

    return "\n".join(patterns)


# ==================================================
# 3. GENERATE LOCAL RECOMMENDATIONS
# ==================================================

def generate_recommendations(error_text):

    error = error_text.lower()

    if "database" in error or "connection" in error:

        return [
            "Check the number of active database connections.",
            "Inspect database connection pool usage.",
            "Check whether the database connection limit is reached.",
            "Examine application logs for connection timeout errors.",
            "Check database server health and response time."
        ]

    elif "redis" in error or "cache" in error:

        return [
            "Check whether the Redis server is running.",
            "Verify Redis connectivity.",
            "Inspect Redis memory usage.",
            "Check cache hit and miss rates.",
            "Examine Redis logs for errors."
        ]

    elif "queue" in error or "message" in error:

        return [
            "Check the message queue backlog.",
            "Inspect the number of active workers.",
            "Check whether messages are being processed.",
            "Examine failed messages.",
            "Monitor queue processing speed."
        ]

    else:

        return [
            "Check the affected service health.",
            "Examine application logs.",
            "Identify the possible root cause.",
            "Check recent deployments or configuration changes.",
            "Monitor the service for further errors."
        ]


# ==================================================
# 4. FORMAT HISTORICAL INCIDENTS
# ==================================================

def format_historical_incidents(incidents):

    if not incidents:
        return "No similar historical incidents found."

    similar_text = []

    for incident in incidents:

        similar_text.append(f"""
Incident ID: {incident.get('id', 'Unknown')}
Service: {incident.get('service', 'Unknown')}
Symptoms: {incident.get('symptoms', 'Unknown')}
Root Cause: {incident.get('root_cause', 'Unknown')}
Successful Fix: {incident.get('fix_worked', 'Unknown')}
Failed Fixes: {incident.get('fixes_failed', 'Unknown')}
""")

    return "\n".join(similar_text)


# ==================================================
# 5. GENERATE INCIDENT BRIEFING
# ==================================================

def generate_briefing(error_text, incidents, patterns):

    print("\nGenerating AI incident analysis...\n")

    similar_text = format_historical_incidents(incidents)

    try:

        # Call Groq AI through llm.py
        ai_analysis = generate_ai_analysis(
            error_text,
            incidents
        )

        briefing = f"""
==================================================
          INCIDENT RESPONSE BRIEFING
==================================================

1. REPORTED PRODUCTION ERROR

{error_text}


2. SIMILAR HISTORICAL INCIDENTS

{similar_text}


3. LEARNED PATTERNS

{patterns}


4. AI-GENERATED INCIDENT ANALYSIS

{ai_analysis}


==================================================
                END OF BRIEFING
==================================================
"""

    except Exception as error:

        print("\nGroq AI error:", error)
        print("Switching to local recommendations...")

        recommendations = generate_recommendations(error_text)

        recommendation_text = "\n".join(
            "- " + item for item in recommendations
        )

        briefing = f"""
==================================================
          INCIDENT RESPONSE BRIEFING
==================================================

1. REPORTED PRODUCTION ERROR

{error_text}


2. SIMILAR HISTORICAL INCIDENTS

{similar_text}


3. LEARNED PATTERNS

{patterns}


4. LOCAL RECOMMENDED NEXT STEPS

{recommendation_text}


5. CONFIDENCE AND LIMITATIONS

Groq AI analysis is unavailable.

Local recommendations are based on incident keywords.
Historical incidents are references, not confirmed
root causes.

Verify all findings before applying production fixes.


==================================================
                END OF BRIEFING
==================================================
"""

    return briefing


# ==================================================
# 6. MAIN INCIDENT RESPONSE FUNCTION
# ==================================================

def respond_to_incident(error_text):

    if not isinstance(error_text, str):
        raise TypeError(
            "Error description must be a string."
        )

    if not error_text.strip():
        raise ValueError(
            "Error description cannot be empty."
        )

    print("\nIncident received!")

    print("Searching local historical incidents...\n")

    try:

        incidents = find_local_incidents(
            error_text,
            limit=5
        )

        print(
            "Historical incidents found:",
            len(incidents)
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError
    ) as error:

        print("Local incident database error:", error)

        incidents = []

    patterns = learn_local_patterns(incidents)

    return generate_briefing(
        error_text,
        incidents,
        patterns
    )


# ==================================================
# 7. RUN THE AGENT
# ==================================================

if __name__ == "__main__":

    try:

        production_error = (
            "Database connection timeout in payment-service. "
            "Customer orders are failing."
        )

        result = respond_to_incident(production_error)

        print(result)

    except Exception as error:

        print("\nINCIDENT AGENT ERROR:", error)