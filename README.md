# Multi-Agent AI Interview Panel Simulator

A simulated interview panel made of 4 independent AI agents (Technical, HR/Culture,
Hiring Manager, Skeptic) that each evaluate a candidate on their own, then debate
each other's conclusions, and finally reach a reasoned (not averaged) hiring decision.

## Chosen Vertical

Candidate evaluation for a technical role (e.g. Backend Developer), using a resume
and an interview transcript as input.

## Approach & Logic

1. **Candidate Profile Builder** reads the raw resume and transcript text and
   extracts a shared, structured profile (skills, experience, claims made, and
   verbatim transcript excerpts to use as citable evidence).
2. **Four independent agents** — Technical, HR/Culture, Hiring Manager, and
   Skeptic — each receive *only* the candidate profile, in **separate, isolated
   API calls**. None of them can see each other's opinions at this stage. Each
   agent must back its opinion with a direct quote/fact from the profile.
3. **Debate step**: all four opinions are given to a debate step that forces
   agents to respond directly to each other's specific points — agreeing,
   disagreeing, or revising their confidence — rather than just repeating
   their original opinion side by side.
4. **Final Decision Engine**: reads the profile, the four opinions, and the
   debate transcript, and produces a final recommendation with an explicit
   weighting *reasoning* — this is deliberately **not** a numeric average of
   the four confidence scores.
5. **Final Report**: recommendation, confidence, strengths, concerns, and any
   disagreement between agents that debate didn't fully resolve.

## How the Solution Works (technical)

- **Backend**: Python + FastAPI (`backend/`). One endpoint (`/run-panel`)
  runs the full pipeline: profile → 4 isolated agent calls → debate →
  final decision, and returns everything as JSON.
- **Frontend**: plain HTML/CSS/JS (`frontend/`), no build tools required.
  It calls the backend API and renders each stage of the pipeline.
- **LLM**: Anthropic Claude API, called once per agent per stage. Every
  agent uses the *same* underlying model with a *different system prompt*,
  which is what defines its role — this keeps the isolation between agents
  easy to verify by reading the code (see `backend/agents.py`).
- **Mock mode**: if no API key is set, the backend returns realistic
  pre-written responses so the entire pipeline can be tested for free.
  Set a real `ANTHROPIC_API_KEY` in `backend/.env` to use the real API.

## Assumptions Made

- Resume and transcript are provided as plain text (not file uploads or audio).
- One candidate is evaluated per run; no persistence/database across sessions.
- No authentication — this is a single-user local tool built for a hackathon demo.
- The debate step runs a fixed set of exchanges rather than an open-ended
  back-and-forth, to keep runtime and API cost predictable during a demo.

## Tech Stack

- Backend: Python 3, FastAPI, Anthropic Python SDK
- Frontend: HTML, CSS, vanilla JavaScript (no framework, no build step)

## Running the Project Locally

See `SETUP_GUIDE.md` for a complete beginner-friendly walkthrough (installing
Python, Git, creating the GitHub repo, and running the app). Quick version:

```bash
# 1. Backend
cd backend
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env if you have a real API key
uvicorn main:app --reload --port 8000

# 2. Frontend (in a second terminal)
cd frontend
python3 -m http.server 5500
```

Then open `http://localhost:5500` in your browser.

## Project Structure

```
interview-panel/
├── backend/
│   ├── main.py           # FastAPI app + API endpoints
│   ├── agents.py         # All agent prompts + orchestration logic
│   ├── llm_client.py     # Anthropic API wrapper + mock mode
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── .gitignore
├── README.md
└── SETUP_GUIDE.md
```
