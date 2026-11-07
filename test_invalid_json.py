import agent

incidents = agent.find_local_incidents(
    "Database connection timeout"
)

if len(incidents) >= 2:
    print("TEST PASSED: Multiple similar incidents found.")

    for incident in incidents:
        print("Incident ID:", incident.get("id"))

else:
    print("TEST FAILED: Multiple incidents were not found.")
    print("Incidents found:", len(incidents))