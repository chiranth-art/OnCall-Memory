"""
Groq AI Integration with Accurate Historical Incident Retrieval
"""

import os
import json

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


# ==================================================
# 1. HISTORICAL INCIDENT RETRIEVAL
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
                "Retrieve exact historical incident records, "
                "including service, symptoms, root causes, "
                "successful fixes and failed fixes."
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

    if not isinstance(error_text, str) or not error_text.strip():
        raise ValueError("Incident description cannot be empty.")

    if not isinstance(historical_incidents, list):
        raise ValueError("Historical incidents must be a list.")

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("Groq API key not found.")

    client = Groq(api_key=api_key)

    available_ids = [
        incident["id"]
        for incident in historical_incidents
        if isinstance(incident, dict)
        and isinstance(incident.get("id"), str)
    ]

    if not available_ids:
        raise ValueError("No valid historical incident IDs found.")

    # ==================================================
    # 4. AI INSTRUCTIONS
    # ==================================================

    system_prompt = """
You are an accurate and careful Incident Response Agent.

Your responsibility is to help engineers investigate
production incidents using historical records and
technical reasoning.

STRICT HISTORICAL ACCURACY RULES:

1. Always retrieve historical incidents using the
   provided function.

2. Retrieved incident records are the source of truth
   for historical information.

3. Never invent, assume, modify or exaggerate
   historical information.

4. Report each incident's recorded:
   - Incident ID
   - Service
   - Symptoms
   - Root cause
   - Successful fix
   - Failed fixes

5. Never attribute information from one incident
   to another.

6. Never claim that an incident experienced a traffic
   spike unless its own record explicitly says so.

7. If a field is missing or empty, write "Not recorded".

8. Never fill missing historical information using
   general technical knowledge.

EVIDENCE AND REASONING RULES:

9. Clearly distinguish between:

   Historical fact:
   Information explicitly present in retrieved records.

   Current observation:
   Information supplied about the current incident.

   Possible cause:
   A technical hypothesis requiring investigation.

   Confirmed cause:
   A cause supported by actual current evidence.

10. General technical knowledge may be used to suggest
    possible causes, but never as historical evidence.

11. Never claim a possible cause is confirmed without
    supporting evidence.

12. Never invent live logs, metrics, traffic statistics,
    monitoring results or configuration values.

13. Never assume a historical fix will solve the
    current incident.

14. Do not provide unsupported confidence percentages.

15. Explain confidence using available evidence
    and its limitations.

TECHNICAL ACCURACY RULES:

16. Distinguish application connection-pool exhaustion
    from database-wide connection-limit exhaustion.

17. Do not assume the database type.

18. Only provide database-specific commands when
    the database type is known.

19. Do not invent pool sizes, database limits,
    timeout values or monitoring measurements.

20. Recommend testing changes in a controlled
    environment before production deployment.

21. Never recommend repeating a failed historical fix
    as though it were a successful solution.

OUTPUT REQUIREMENTS:

Prepare the briefing using these six sections:

1. Possible root causes
2. Historical incident comparison
3. Ordered investigation steps
4. Possible solutions after verification
5. Confidence and limitations
6. Next immediate actions

For historical comparisons, include all available records.

Use these fields:
- Incident ID
- Service
- Recorded symptoms
- Recorded root cause
- Recorded successful fix
- Recorded failed fixes

If information is missing, write "Not recorded".

Prioritize factual accuracy, evidence-based reasoning
and safe incident investigation.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"""
CURRENT INCIDENT:

{error_text}

AVAILABLE HISTORICAL INCIDENT IDs:

{json.dumps(available_ids)}

Retrieve all available historical incidents using
the provided function.

Prepare the incident briefing using the six required
sections.

IMPORTANT:

- Include all available historical incidents.
- Do not invent missing information.
- INC-001 mentions a traffic spike in its symptoms.
- INC-002 does not mention a traffic spike.
- Do not transfer information between incidents.
- Clearly label general technical suggestions
  as possible causes.
- Do not claim to have accessed live logs or metrics.
- Do not assume a database type.
"""
        }
    ]

    # ==================================================
    # 5. REQUEST FUNCTION CALLING
    # ==================================================

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=tools,
            tool_choice="required",
            temperature=0.2
        )

    except Exception as error:
        raise RuntimeError(
            f"Groq function-calling request failed: {error}"
        ) from error

    message = response.choices[0].message

    if not message.tool_calls:
        raise RuntimeError(
            "AI did not call the historical incident function."
        )

    # Convert the assistant message into a standard dictionary.
    messages.append(
        message.model_dump(exclude_none=True)
    )

    # ==================================================
    # 6. EXECUTE REQUESTED FUNCTIONS
    # ==================================================

    retrieved_ids = set()

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

        retrieved_ids.update(incident_ids)

        function_result = get_historical_incidents(
            incident_ids,
            historical_incidents
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
    # 7. VERIFY HISTORICAL RETRIEVAL
    # ==================================================

    missing_ids = set(available_ids) - retrieved_ids

    if missing_ids:
        raise RuntimeError(
            "AI did not retrieve all available incidents: "
            + ", ".join(sorted(missing_ids))
        )

    # ==================================================
    # 8. GENERATE FINAL ANALYSIS
    # ==================================================

    try:

        final_response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.2
        )

    except Exception as error:
        raise RuntimeError(
            f"Groq analysis generation failed: {error}"
        ) from error

    result = final_response.choices[0].message.content

    if not result or not result.strip():
        raise RuntimeError(
            "AI returned an empty analysis."
        )

    return result