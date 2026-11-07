
"""
api.py
IncidentIQ - FastAPI Backend

Connects the React frontend to the existing
Hindsight + Groq incident response agent.
"""

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import memory
from agent import respond_to_incident
from load_incidents import INCIDENTS


# ==================================================
# 1. APPLICATION LIFECYCLE
# ==================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("IncidentIQ API started.")
    yield
    memory.close_client()
    print("IncidentIQ API stopped.")


app = FastAPI(
    title="IncidentIQ API",
    description="AI-powered incident response backend",
    version="1.0.0",
    lifespan=lifespan
)


# ==================================================
# 2. CORS CONFIGURATION
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ==================================================
# 3. REQUEST MODELS
# ==================================================

class AnalyzeRequest(BaseModel):
    error: str = Field(min_length=1)
    service: Optional[str] = None
    logs: Optional[str] = None
    severity: Optional[str] = "medium"


class ReflectRequest(BaseModel):
    question: str = Field(min_length=1)


class OutcomeRequest(BaseModel):
    incident_id: str = Field(min_length=1)
    outcome: str = Field(min_length=1)
    worked: Optional[bool] = None


# ==================================================
# 4. HEALTH CHECK
# ==================================================

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "application": "IncidentIQ",
        "hindsight_available": memory.hindsight_available
    }


# ==================================================
# 5. INCIDENT ANALYSIS
# ==================================================

@app.post("/api/analyze")
def analyze_incident(request: AnalyzeRequest):

    error_text = request.error.strip()

    if not error_text:
        raise HTTPException(
            status_code=400,
            detail="Incident description cannot be empty."
        )

    # Combine the supplied context for the existing agent.
    incident_context = f"""
Current incident:
{error_text}

Affected service:
{request.service or "Not specified"}

Severity reported by engineer:
{request.severity or "Not specified"}

Additional production logs:
{request.logs or "Not provided"}
"""

    try:
        analysis = respond_to_incident(incident_context)

        return {
            "status": "success",
            "analysis": analysis,
            "incident": {
                "error": error_text,
                "service": request.service,
                "severity": request.severity
            }
        }

    except Exception as error:
        print("Incident analysis failed:", error)

        raise HTTPException(
            status_code=500,
            detail="Incident analysis failed. Check backend configuration."
        )


# ==================================================
# 6. HISTORICAL INCIDENTS
# ==================================================

@app.get("/api/incidents")
def get_incidents():

    try:
        return {
            "status": "success",
            "total": len(INCIDENTS),
            "incidents": INCIDENTS
        }

    except Exception as error:
        print("Incident retrieval failed:", error)

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve historical incidents."
        )


# ==================================================
# 7. MEMORY REFLECTION
# ==================================================

@app.post("/api/reflect")
def reflect_patterns(request: ReflectRequest):

    try:
        answer = memory.learned_patterns(
            request.question.strip()
        )

        return {
            "status": "success",
            "question": request.question,
            "answer": answer
        }

    except Exception as error:
        print("Memory reflection failed:", error)

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve memory insights."
        )


# ==================================================
# 8. RESOLUTION FEEDBACK
# ==================================================

@app.post("/api/outcome")
def submit_outcome(request: OutcomeRequest):

    try:
        result = memory.save_outcome(
            incident_id=request.incident_id,
            outcome=request.outcome,
            worked=request.worked
        )

        return {
            "status": "success",
            "message": "Resolution feedback saved.",
            "incident_id": request.incident_id,
            "saved": bool(result)
        }

    except Exception as error:
        print("Outcome saving failed:", error)

        raise HTTPException(
            status_code=500,
            detail="Could not save resolution feedback."
        )
