"""
Groq AI Integration with Accurate Historical Incident Retrieval
"""

import os
import json

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


# ==================================================
# 1. HISTORICAL INCIDENT RETRIEVAL FUNCTION
# ==================================================

def get_historical_incidents(incident_ids, historical_incidents):

    if not isinstance(incident_ids, list):
        raise ValueError("Incident IDs must be a list.")

    if not all(isinstance(item, str) for item in incident_ids):
        raise ValueError("Every incident ID must be a string.")

    results = []

    for incident in historical_incidents:

        if not isinstance(incident, dict):
            continue

        if incident.get("id") in incident_ids:
            results.append(incident)

    return results


# ==================================================
# 2. FUNCTION CALLING DEFINITION
# ==================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_historical_incidents",
            "description": (
                "Retrieve the exact historical incident records, "
                "including their recorded root causes and fixes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_ids": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["incident_ids"],
                "additionalProperties": False
            }
        }
    }
]


# ==================================================
# 3. GENERATE AI ANALYSIS
# ==================================================

def generate_ai_analysis(error_text, historical_incidents):

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("Groq API key not found.")

    client = Groq(api_key=api_key)

    available_ids = [
        incident.get("id")
        for incident in historical_incidents
        if isinstance(incident, dict)
        and isinstance(incident.get("id"), str)
    ]

    messages = [
        {
            "role": "system",
            "content": """
You are an Incident Response Agent.

IMPORTANT ACCURACY RULES:

1. Use the historical incident retrieval function.
2. Treat retrieved incident records as the source of truth.
3. Never invent historical root causes or successful fixes.
4. Report successful fixes exactly according to the
   historical record's fix_worked field.
5. Do not confuse a database connection limit with
   an application connection-pool limit.
6. Do not assume a historical fix will solve the
   current incident.
7. Never invent live logs, metrics or monitoring data.
8. Do not provide unsupported confidence percentages.
9. Clearly distinguish possible causes from confirmed causes.
10. Recommend verification before production changes.
"""
        },
        {
            "role": "user",
            "content": f"""
CURRENT INCIDENT:

{error_text}

AVAILABLE HISTORICAL INCIDENT IDs:

{json.dumps(available_ids)}

Retrieve the available historical incidents using
the provided function.

Then prepare an incident analysis with these sections:

1. Possible root causes
2. Historical incident comparison
3. Ordered investigation steps
4. Possible solutions after verification
5. Confidence and limitations
6. Next immediate actions

For every historical incident, accurately report:
- Incident ID
- Recorded root cause
- Recorded successful fix
- Recorded failed fixes

If information is missing, say it is not recorded.

Do not invent evidence or claim that a possible
root cause has been confirmed.
"""
        }
    ]

    # ==================================================
    # 4. REQUEST FUNCTION CALLING
    # ==================================================

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.2
    )

    message = response.choices[0].message

    if not message.tool_calls:
        raise RuntimeError(
            "AI did not call the historical incident function."
        )

    messages.append(message)

    # ==================================================
    # 5. EXECUTE REQUESTED FUNCTIONS
    # ==================================================

    for tool_call in message.tool_calls:

        function_name = tool_call.function.name

        if function_name != "get_historical_incidents":
            raise ValueError(
                f"Unknown function: {function_name}"
            )

        try:

            arguments = json.loads(
                tool_call.function.arguments
            )

        except (json.JSONDecodeError, TypeError):

            raise ValueError(
                "Invalid JSON function arguments."
            )

        if not isinstance(arguments, dict):
            raise ValueError(
                "Function arguments must be a JSON object."
            )

        if set(arguments.keys()) != {"incident_ids"}:
            raise ValueError(
                "Unexpected function arguments."
            )

        incident_ids = arguments["incident_ids"]

        if not isinstance(incident_ids, list):
            raise ValueError(
                "Incident IDs must be a list."
            )

        if not all(
            isinstance(item, str)
            for item in incident_ids
        ):
            raise ValueError(
                "Incident IDs must contain strings only."
            )

        unknown_ids = set(incident_ids) - set(available_ids)

        if unknown_ids:
            raise ValueError(
                f"Unknown incident IDs requested: {unknown_ids}"
            )

        try:

            function_result = get_historical_incidents(
                incident_ids,
                historical_incidents
            )

        except Exception as error:

            raise RuntimeError(
                f"Historical retrieval failed: {error}"
            )

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(
                function_result,
                ensure_ascii=False
            )
        })

    # ==================================================
    # 6. GENERATE FINAL ANALYSIS
    # ==================================================

    final_response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0.2
    )

    result = final_response.choices[0].message.content

    if not result:
        raise RuntimeError(
            "AI returned an empty analysis."
        )

    return result