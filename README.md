# OnCall-Memory

> **An incident response agent that gives on-call engineers access to lessons from previous production incidents.**  
> Built with [Hindsight](https://github.com/vectorize-io/hindsight) for agent memory and Groq for incident analysis.

[![Hindsight](https://img.shields.io/badge/Memory-Hindsight-6f42c1)](https://github.com/vectorize-io/hindsight)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b)](https://streamlit.io/)

---

## The problem

It is 9 PM on a Friday. A food-delivery platform starts failing to process customer orders. The on-call engineer, Arjun, sees:

```text
Database connection timeout in payment-service.
Customer orders are failing.
```

A similar issue happened before. The useful information is buried in incident records: what caused the outage, which mitigation worked, and which attempts failed. Under pressure, searching through old tickets and post-mortems wastes valuable time—and repeating a failed fix can make the incident worse.

**OnCall-Memory helps Arjun investigate by retrieving relevant historical incident knowledge and turning it into a structured briefing.**

Instead of starting from zero, the engineer can review what happened in similar incidents, compare the recorded root causes and fixes, and decide what to verify in the current environment.

## What OnCall-Memory does

1. **Accepts an incident description** through a Streamlit interface.
2. **Recalls related memories** from a Hindsight memory bank.
3. **Resolves recalled incident IDs** to the corresponding structured incident records in the project.
4. **Uses local keyword matching as a fallback** if Hindsight is unavailable or retrieval fails.
5. **Generates an investigation briefing** with Groq, using the available historical records as evidence.
6. **Keeps the engineer in control**: the agent provides guidance; it does not execute production changes.

## Example: Arjun investigates a payment outage

Arjun enters the database timeout message into the application.

The repository's fictional food-delivery incident dataset includes several related payment-service incidents:

| Incident | Recorded symptoms / cause | Recorded outcome |
|---|---|---|
| `INC-001` | Database connection timeout after a dinner-rush traffic spike; connection pool exhausted (limit 50) | Increasing the pool from 50 to 200 worked; restarting the service failed when the issue returned within 10 minutes |
| `INC-005` | A later timeout caused by a long-running query missing a database index | Adding the missing index and keeping the pool at 200 worked; restarting and raising the pool alone were insufficient |
| `INC-013` | A connection leak in the refund handler exhausted the pool | Closing connections in a `finally` block and keeping the pool at 200 worked; restarting and raising the pool alone did not stop the leak |

These records illustrate why historical context matters: similar symptoms do not always mean the same root cause. The agent is instructed to distinguish recorded historical facts from possible causes that still need investigation.

**Data note:** The repository's incident records are fictional demonstration data. They do not establish that a real production outage was resolved in five minutes. The current dataset records incident dates and outcomes; it does not contain Runbook A / Runbook B fields, so this README does not claim that the application compares those runbooks.

## How it works

```text
                  On-call engineer
                         |
                         v
               Streamlit incident form
                         |
                         v
              respond_to_incident()
                    (agent.py)
                         |
                         v
               retrieve_historical_incidents()
                         |
              +----------+-----------+
              |                      |
              v                      v
        Hindsight recall       Local keyword fallback
          (memory.py)            (agent.py)
              |                      |
              +----------+-----------+
                         |
                         v
             Match recalled incident IDs
              to canonical incident data
                         |
                         v
              Groq incident analysis
                   (llm.py)
                         |
                         v
              Structured investigation
                    briefing
                         |
                         v
                Engineer reviews
                and decides actions
```

### Main components

| File | Responsibility |
|---|---|
| `app.py` | Streamlit user interface; accepts an incident description and displays the investigation report |
| `agent.py` | Orchestrates incident response, Hindsight recall, incident-ID matching, local fallback, and analysis |
| `memory.py` | Initializes the Hindsight client and implements retain, recall, outcome feedback, reflection, retries, and local JSON fallback |
| `load_incidents.py` | Defines the fictional historical incident dataset and loads incidents/outcomes into Hindsight |
| `llm.py` | Calls Groq and creates the evidence-focused incident briefing |
| `sample_incidents.json` | Small sample incident dataset used by the memory fallback |
| `briefing.py` | Additional briefing implementation in the repository |
| `test_*.py` | Tests for imports, memory integration, retries, deduplication, reflection, feedback, and incident handling |

## Hindsight integration

OnCall-Memory uses Hindsight as its long-term memory layer. The integration is implemented in `memory.py`.

### Retain: remember incident knowledge

`save_incident()` formats a structured incident into a memory record. The record includes its ID, date, service, symptoms, root cause, successful fix, failed fixes, and resolution time. When Hindsight is available, the function sends the record to the configured memory bank. The module also has local JSON persistence as a fallback.

`save_outcome()` is used to retain resolution feedback, while `learned_patterns()` supports retrieving patterns from previously stored incident knowledge.

### Recall: find relevant past incidents

When an engineer submits an incident, `agent.py` calls `memory.find_similar()` with the new incident description. The agent extracts incident IDs from the recalled memory text and maps those IDs back to the canonical structured records before sending them to the analysis layer.

This two-step approach is intentional: Hindsight finds potentially relevant memories, while the canonical incident records provide the structured historical fields used in the briefing.

### Resilience

The memory module includes:
- Retry handling for temporary Hindsight operation failures.
- A local JSON memory fallback when Hindsight cannot be initialized or becomes unavailable.
- Duplicate-memory normalization and deduplication helpers.
- A configurable Hindsight bank ID and API base URL.

The agent also has a local keyword-matching fallback for finding incident records when Hindsight recall is unavailable.

## Incident briefing and accuracy

`llm.py` uses Groq to generate the investigation report from the current incident description and the selected historical records. The prompt requires the model to:
- Report historical incident details from the supplied records rather than inventing them.
- Separate current observations, historical facts, possible causes, and confirmed causes.
- Identify successful and failed fixes accurately.
- Mark missing information as “Not recorded”.
- Avoid claiming access to live logs, metrics, or monitoring systems.
- Avoid assuming a database type or inventing configuration values.
- Treat historical fixes as evidence to evaluate, not guaranteed solutions.

The intended briefing contains:
1. Possible root causes
2. Historical incident comparison
3. Ordered investigation steps
4. Possible solutions after verification
5. Confidence and limitations
6. Next immediate actions

The engineer must verify recommendations against current logs, metrics, deployments, and system state before changing production.

## Technology stack

- **Language:** Python
- **User interface:** Streamlit
- **Agent analysis:** Groq API
- **Long-term agent memory:** Hindsight Python client
- **Local fallback:** JSON files
- **Configuration:** Environment variables loaded with `python-dotenv`
- **Tests:** Python test files using pytest-compatible test functions

## Getting started

### Prerequisites

- Python 3.10 or later
- A [Groq API key](https://console.groq.com/keys)
- A [Hindsight API key / account](https://hindsight.vectorize.io/) for cloud memory

### 1. Clone the repository

```bash
git clone https://github.com/chiranth-art/OnCall-Memory.git
cd OnCall-Memory
```

### 2. Create and activate a virtual environment

**Windows PowerShell**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

The repository currently does not include a committed dependency lockfile or `requirements.txt`. Install the packages imported by the application:

```bash
pip install streamlit groq hindsight-client python-dotenv certifi pytest
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
HINDSIGHT_API_KEY=your_hindsight_api_key

# Optional: defaults are shown below
HINDSIGHT_BANK_ID=oncall-memory
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
```

Keep `.env` private. Do not commit API keys or other secrets to GitHub.

### 5. Load the historical incidents into Hindsight

Run the loader once:

```bash
python load_incidents.py
```

The loader uses a marker file (`.incidents_loaded`) to avoid accidentally inserting the same sample incidents repeatedly. Only use `--force` if you intentionally want to load the dataset again:

```bash
python load_incidents.py --force
```

This step is important for a Hindsight-backed demo: it retains the sample incident records and associated outcome feedback in the configured Hindsight bank.

### 6. Start the application

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`).

## Try it

Paste an incident such as:

```text
Database connection timeout in payment-service.
Customer orders are failing.
```

Select **Analyse Incident**.

The application calls `respond_to_incident()` and displays the resulting investigation report. When Hindsight is configured and has relevant memories loaded, the agent attempts Hindsight recall first. If Hindsight is unavailable, it can use local keyword matching against the canonical incident records.

For the demo, show the actual report and the real Hindsight-backed retrieval path from your running environment. Do not replace live output with a fabricated result.

## Running tests

Run the repository's tests from the project root:

```bash
python -m pytest -v
```

The repository includes tests covering areas such as:
- Module imports
- Multiple incident handling
- Hindsight memory integration
- Invalid JSON handling
- Deduplication
- Retry behavior
- Outcome feedback
- Reflection / learned patterns
- Groq integration

Test results depend on the environment and configured credentials. Do not describe tests as passing unless they have been run successfully.

## Repository structure

```text
OnCall-Memory/
├── agent.py
├── app.py
├── briefing.py
├── llm.py
├── load_incidents.py
├── memory.py
├── sample_incidents.json
├── test_deduplication.py
├── test_groq.py
├── test_imports.py
├── test_invalid_json.py
├── test_memory_integration.py
├── test_multiple_incidents.py
├── test_outcome_feedback.py
├── test_reflection.py
└── test_retry.py
```

## Limitations and responsible use

- The included incident records are fictional sample data, not a connection to a company's live incident-management system.
- The app does not automatically inspect production logs, metrics, traces, Slack, or ticketing systems.
- Hindsight recall can return no relevant memories; the local fallback is keyword-based and may not find every semantically related incident.
- Historical fixes may not apply to the current deployment or infrastructure.
- The agent does not execute production changes. Engineers remain responsible for diagnosis, verification, approvals, and remediation.
- Runbook A / Runbook B comparison is not represented in the current incident schema.
- The repository does not currently include a committed `requirements.txt`; dependencies are listed above for setup.

## Project links

- **Project repository:** https://github.com/chiranth-art/OnCall-Memory
- **Hindsight GitHub:** https://github.com/vectorize-io/hindsight
- **Hindsight documentation:** https://hindsight.vectorize.io/
- **Vectorize — Agent Memory:** https://vectorize.io/what-is-agent-memory

---

**OnCall-Memory — helping incident responders reuse what their systems have already learned.**
