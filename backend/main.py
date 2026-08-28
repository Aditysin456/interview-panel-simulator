"""
main.py
FastAPI backend for the Multi-Agent AI Interview Panel Simulator.

Run with:
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import agents

app = FastAPI(title="Multi-Agent Interview Panel Simulator")

# Allow the local frontend (opened as a plain HTML file or via a simple
# static server) to call this API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PanelRequest(BaseModel):
    resume_text: str
    transcript_text: str


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Interview Panel Simulator backend is running."}


@app.post("/build-profile")
def build_profile(req: PanelRequest):
    profile = agents.build_profile(req.resume_text, req.transcript_text)
    return {"profile": profile}


@app.post("/run-panel")
def run_panel(req: PanelRequest):
    """
    Runs the FULL pipeline in one call:
    1. Build candidate profile
    2. Run 4 independent agents (isolated calls)
    3. Run the debate step
    4. Run the final decision engine
    Returns everything so the frontend can display each stage.
    """
    if not req.resume_text.strip() or not req.transcript_text.strip():
        return {"error": "resume_text and transcript_text cannot be empty"}

    # Step 0
    profile = agents.build_profile(req.resume_text, req.transcript_text)

    # Step 1 - each agent is called independently, no shared context between them
    opinions = agents.run_all_independent_agents(profile)

    # Step 2 - debate
    debate = agents.run_debate(opinions)

    # Step 3 - final decision (weighted reasoning, not an average)
    final_decision = agents.run_final_decision(profile, opinions, debate)

    return {
        "profile": profile,
        "independent_opinions": opinions,
        "debate": debate,
        "final_decision": final_decision,
    }
