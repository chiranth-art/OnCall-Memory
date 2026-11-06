
"""
briefing.py - Evidence-based AI incident briefing generator.

Workflow:
    1. Retrieve memories from Hindsight.
    2. Group near-duplicate memories.
    3. Label each evidence group.
    4. Ask Groq to generate a grounded incident briefing.
    5. Fall back to retrieved evidence if Groq fails.
"""

import os
import re
import time
from difflib import SequenceMatcher
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from memory import find_similar


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)


# --------------------------------------------------
# MEMORY NORMALIZATION AND GROUPING
# --------------------------------------------------

def _normalize_memory(memory: str) -> str:
    """
    Normalize memory text for duplicate comparison.

    Removes metadata differences such as:
    When: 2026-09-20 | Where: checkout-web
    """

    text = memory.casefold()

    text = re.sub(
        r"\|\s*when:\s*\d{4}-\d{2}-\d{2}",
        "",
        text
    )

    text = re.sub(
        r"\|\s*where:\s*[^|]+",
        "",
        text
    )

    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _similarity(first: str, second: str) -> float:
    """
    Compare two normalized memories.

    Combines word overlap and sequence similarity.
    """

    first_words = set(first.split())
    second_words = set(second.split())

    if not first_words or not second_words:
        return 0.0

    intersection = len(first_words & second_words)
    union = len(first_words | second_words)

    jaccard = intersection / union

    sequence = SequenceMatcher(
        None,
        first,
        second
    ).ratio()

    return max(jaccard, sequence)


def _group_memories(
    memories: list[str],
    threshold: float = 0.68
) -> list[dict[str, Any]]:
    """
    Group near-duplicate memories.

    Each group retains its original memory references.
    Different fixes and different incidents are preserved
    unless their descriptions are sufficiently similar.
    """

    groups = []

    for index, memory in enumerate(memories, start=1):

        if not isinstance(memory, str) or not memory.strip():
            continue

        normalized = _normalize_memory(memory)

        if not normalized:
            continue

        matched_group = None

        for group in groups:

            similarity = _similarity(
                normalized,
                group["normalized"]
            )

            if similarity >= threshold:
                matched_group = group
                break

        if matched_group:

            matched_group["references"].append(
                f"Memory {index}"
            )

            matched_group["originals"].append(memory)

        else:

            groups.append({
                "normalized": normalized,
                "references": [f"Memory {index}"],
                "originals": [memory]
            })

    return groups


def _format_memory_context(
    groups: list[dict[str, Any]]
) -> str:
    """
    Format grouped evidence for Groq.

    Original memory text is retained rather than replaced
    with an AI-generated summary.
    """

    sections = []

    for index, group in enumerate(groups, start=1):

        references = ", ".join(group["references"])

        evidence = "\n".join(
            f"- {memory}"
            for memory in group["originals"]
        )

        sections.append(
            f"EVIDENCE GROUP {index}\n"
            f"References: {references}\n"
            f"Original evidence:\n{evidence}"
        )

    return "\n\n".join(sections)


# --------------------------------------------------
# SYSTEM PROMPT
# --------------------------------------------------


SYSTEM_PROMPT = """
You are OnCall Memory, an evidence-based incident response assistant.

Use only the current error and supplied Hindsight memories.

STRICT EVIDENCE RULES:

1. Never invent incident IDs, dates, services, root causes,
   resolutions, metrics, or historical events.

2. Cite evidence using the exact references supplied,
   such as [Memory 1] or [Memory 3].

3. Never create fake IDs or treat memory numbers as incident IDs.

4. Distinguish DIRECT MATCH, INDIRECT SIMILARITY,
   and NO RELEVANT MATCH.

5. Similar symptoms do not prove identical root causes.

6. Grouped descriptions may refer to the same incident.
   Never count duplicate descriptions as independent incidents.

7. A successful fix for one technology must not automatically
   be recommended for a different technology.

8. For INDIRECT SIMILARITY, do not transfer a historical fix
   as a proven recommendation for the current problem.

9. You may mention an indirect fix only as an investigation
   idea, explicitly stating that it has not been validated
   for the current problem.

10. A fix is historically successful only when the supplied
    memory explicitly records that it worked.

11. A failed fix must be described with its actual recorded
    context. Do not claim it always fails.

12. Do not combine fixes from different incidents and claim
    that the combination was successful unless the evidence
    explicitly records that combination.

13. Do not invent alternative solutions or present general
    technical knowledge as historical evidence.

14. Separate historical facts from current hypotheses.

15. If there is no directly relevant successful fix,
    explicitly say so.

16. Never claim that a fix has been executed or verified.

OUTPUT STRUCTURE:

MATCH:
Classify the evidence as DIRECT MATCH, INDIRECT SIMILARITY,
or NO RELEVANT MATCH. Explain why and cite references.

LIKELY ROOT CAUSE:
State only what the evidence supports.
Label possible explanations as hypotheses.

TRY FIRST:
List successful fixes only when they are supported by
directly relevant historical evidence.

For indirect matches, provide investigation suggestions
only, clearly labelled as unverified suggestions.

If no relevant successful fix exists, say so.

DO NOT TRY:
List historically failed fixes and their actual context.
Do not generalize beyond the evidence.

PATTERN:
Describe recurring patterns only when supported by
the retrieved memories.

CONFIDENCE:
Use HIGH, MEDIUM, or LOW.

HIGH:
Requires strong, directly relevant evidence, including
a documented successful outcome.

MEDIUM:
Requires relevant evidence, but some uncertainty remains.

LOW:
Use when evidence is indirect, incomplete, or contradictory.

Do not use HIGH confidence for an indirect match.

Keep the briefing concise, practical, and honest.
"""



# --------------------------------------------------
# FALLBACK RESPONSE
# --------------------------------------------------

NO_MATCH_TEXT = """
No matching past incidents were found in Hindsight memory.

No historical fix can currently be recommended with confidence.

Suggested investigation steps:

1. Inspect the current application logs.
2. Identify the affected service and dependencies.
3. Check monitoring metrics and recent deployments.
4. Record the actual root cause and resolution.
5. Save the incident to Hindsight for future learning.
"""


# --------------------------------------------------
# RESPONSE CLEANING
# --------------------------------------------------

def _clean(text: str) -> str:
    """Remove hidden reasoning tags and clean the response."""

    if not isinstance(text, str):
        return ""

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    return text.strip()


# --------------------------------------------------
# GROQ REQUEST
# --------------------------------------------------

def _ask_groq(
    error_text: str,
    memories: list[str],
    attempts: int = 3
) -> str:

    if not isinstance(error_text, str) or not error_text.strip():
        raise ValueError("error_text must be a non-empty string.")

    if not isinstance(memories, list):
        raise TypeError("memories must be a list.")

    if (
        not isinstance(attempts, int)
        or isinstance(attempts, bool)
        or attempts < 1
    ):
        raise ValueError("attempts must be a positive integer.")

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to your .env file."
        )

    groups = _group_memories(memories)

    if not groups:
        raise ValueError("No valid incident memories were provided.")

    memory_context = _format_memory_context(groups)

    groq_client = Groq(api_key=api_key)

    user_prompt = f"""
CURRENT PRODUCTION ERROR:

{error_text}

GROUPED HINDSIGHT EVIDENCE:

{memory_context}

ANALYSIS INSTRUCTIONS:

1. Compare the current error against the evidence.
2. Identify direct matches and indirect similarities.
3. Do not count duplicate memories as separate incidents.
4. Cite the exact memory references provided.
5. Never invent incident IDs or dates.
6. Recommend only fixes supported by relevant evidence.
7. If the CSS problem has only a CDN-related analogy,
   explicitly state that it is an indirect similarity.

Generate the incident briefing using the required structure.
"""

    for attempt in range(attempts):

        try:

            response = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=0.1,
                max_completion_tokens=1500
            )

            content = response.choices[0].message.content

            briefing = _clean(content or "")

            if briefing:
                return briefing

            raise RuntimeError(
                "Groq returned an empty incident briefing."
            )

        except Exception:

            if attempt == attempts - 1:
                raise

            delay = 1.5 * (attempt + 1)

            print(
                f"Groq request failed. "
                f"Retrying in {delay} seconds "
                f"({attempt + 2}/{attempts})..."
            )

            time.sleep(delay)

    raise RuntimeError("Groq request failed.")


# --------------------------------------------------
# MAIN BRIEFING FUNCTION
# --------------------------------------------------

def generate_briefing(
    error_text: str,
    limit: int = 12
) -> dict[str, Any]:
    """
    Retrieve, group, and analyze historical incident memories.

    Returns:
        {
            "briefing": str,
            "memories": list,
            "grouped_memories": list,
            "used_llm": bool
        }
    """

    if not isinstance(error_text, str) or not error_text.strip():
        raise ValueError("error_text must be a non-empty string.")

    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or limit < 1
    ):
        raise ValueError("limit must be a positive integer.")

    error_text = error_text.strip()

    print("\nSearching Hindsight for similar incidents...")

    memories = find_similar(
        error_text,
        limit=limit
    )

    if not memories:

        print("No matching incidents found.")

        return {
            "briefing": NO_MATCH_TEXT,
            "memories": [],
            "grouped_memories": [],
            "used_llm": False
        }

    groups = _group_memories(memories)

    print(f"Retrieved memories: {len(memories)}")
    print(f"Evidence groups after grouping: {len(groups)}")

    try:

        print("Generating evidence-based briefing with Groq...")

        briefing = _ask_groq(
            error_text=error_text,
            memories=memories
        )

        return {
            "briefing": briefing,
            "memories": memories,
            "grouped_memories": groups,
            "used_llm": True
        }

    except Exception as error:

        print(f"Groq briefing generation failed: {error}")
        print("Using Hindsight evidence as fallback.")

        fallback = (
            "AI briefing generation is currently unavailable.\n\n"
            "Retrieved historical evidence:\n\n"
            + _format_memory_context(groups)
        )

        return {
            "briefing": fallback,
            "memories": memories,
            "grouped_memories": groups,
            "used_llm": False
        }


# --------------------------------------------------
# DIRECT TEST
# --------------------------------------------------

if __name__ == "__main__":

    from memory import close_client

    test_errors = [
        (
            "Payment service is experiencing database connection "
            "pool exhaustion and connection timeout errors."
        ),
        (
            "Authentication service is failing because Redis "
            "is running out of memory."
        ),
        (
            "Frontend CSS is not loading correctly."
        )
    ]

    try:

        for index, error in enumerate(test_errors, start=1):

            print("\n" + "=" * 60)
            print(f"TEST INCIDENT {index}")
            print("=" * 60)

            print("\nCURRENT ERROR:")
            print(error)

            result = generate_briefing(error)

            print("\nINCIDENT BRIEFING:")
            print(result["briefing"])

            print("\nMEMORY STATISTICS:")
            print("Retrieved:", len(result["memories"]))
            print("Evidence groups:", len(result["grouped_memories"]))
            print("Groq used:", result["used_llm"])

    finally:
        close_client()
