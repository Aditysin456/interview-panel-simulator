"""
llm_client.py
Single place that talks to the Groq API.

MOCK MODE:
If no GROQ_API_KEY is set (or MOCK_MODE=true in .env), this returns
realistic fake responses instead of calling the real API. This lets you
run and test the ENTIRE pipeline (profile -> 4 agents -> debate -> final
decision) for free, before you plug in a real API key.

To use the real API: put your key in backend/.env as
GROQ_API_KEY=gsk_xxxxx

RATE LIMIT HANDLING:
Groq's free tier has a tokens-per-minute (TPM) limit. Since the 4
independent agents now run in parallel, they can briefly exceed that
limit if fired at the exact same moment. If Groq responds with a 429
(rate limit) error, this file automatically waits and retries a few
times before giving up, instead of crashing the whole request.
"""

import os
import random
import time

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY", "")
MOCK_MODE = os.getenv("MOCK_MODE", "").lower() == "true" or not API_KEY
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

_client = None
if not MOCK_MODE:
    from groq import Groq
    _client = Groq(api_key=API_KEY)

MAX_RETRIES = 4


def call_llm(system: str, user: str, max_tokens: int = 1200) -> str:
    """Makes one isolated call to the model. Returns raw text response.
    Automatically retries with a short wait if Groq's rate limit is hit."""
    if MOCK_MODE:
        return _mock_response(system, user)

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = _client.chat.completions.create(
                model=MODEL_NAME,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            error_text = str(e)
            is_rate_limit = "429" in error_text or "rate_limit" in error_text.lower()
            if is_rate_limit and attempt < MAX_RETRIES - 1:
                wait_seconds = 2 * (attempt + 1) + random.uniform(0, 1)
                time.sleep(wait_seconds)
                continue
            raise last_error

    raise last_error


# ---------------------------------------------------------------------
# MOCK RESPONSES — used only when there's no API key, so you can test
# the full app flow end-to-end without spending API credits.
# ---------------------------------------------------------------------

def _mock_response(system: str, user: str) -> str:
    if "Candidate Profile Builder" in system:
        return """{
  "skills": ["Python", "SQL", "React", "Team Leadership"],
  "experience": [
    {"role": "Backend Developer Intern", "company": "TechCorp",
     "duration": "6 months", "highlights": ["Built REST APIs", "Worked with MongoDB"]}
  ],
  "claims": ["Led a team of 5 engineers", "3 years of experience with machine learning"],
  "transcript_excerpts": [
    "I led a team of 5 people during my internship.",
    "I have about 3 years of experience with machine learning, mostly self-taught.",
    "Honestly I only used MongoDB for a couple of weeks on one project."
  ]
}"""

    if "Technical Agent" in system:
        return """{"agent": "technical", "opinion": "Candidate shows basic backend familiarity but claimed ML experience is not well supported by concrete examples.", "confidence": 55, "evidence": ["I have about 3 years of experience with machine learning, mostly self-taught.", "Built REST APIs"]}"""

    if "HR/Culture Agent" in system:
        return """{"agent": "hr_culture", "opinion": "Communicates clearly and mentions leadership experience positively.", "confidence": 70, "evidence": ["I led a team of 5 people during my internship."]}"""

    if "Hiring Manager Agent" in system:
        return """{"agent": "hiring_manager", "opinion": "Reasonable junior candidate overall, though some claims need verification.", "confidence": 60, "evidence": ["Built REST APIs", "Led a team of 5 people during my internship."]}"""

    if "Skeptic Agent" in system:
        return """{"agent": "skeptic", "opinion": "The claim of 3 years of ML experience seems inflated given only a 6-month internship is listed, and the candidate admitted only brief MongoDB use despite listing it as a skill.", "confidence": 80, "evidence": ["Honestly I only used MongoDB for a couple of weeks on one project.", "I have about 3 years of experience with machine learning, mostly self-taught."]}"""

    if "Debate Orchestrator" in system:
        return """{
  "exchanges": [
    {"from": "skeptic", "to": "technical", "message": "You gave 55% confidence on technical skill, but the candidate admitted only using MongoDB briefly while listing it as a core skill. Doesn't that lower your confidence further?", "type": "challenge"},
    {"from": "technical", "to": "skeptic", "message": "That's a fair point, I hadn't weighted the MongoDB admission heavily enough. Lowering my confidence to 40.", "type": "revise", "new_confidence": 40},
    {"from": "hr_culture", "to": "skeptic", "message": "I still think the communication and leadership claim about managing 5 people stands independently of the technical skepticism.", "type": "disagree"}
  ],
  "unresolved_conflicts": ["Whether the leadership claim of managing 5 people is independently verifiable or should also be treated with skepticism."]
}"""

    if "Final Decision Engine" in system:
        return """{
  "recommendation": "Hire with Reservations",
  "confidence": 58,
  "reasoning": "The Skeptic Agent's evidence about inflated technical claims is directly relevant to a technical role and caused the Technical Agent to revise its confidence downward during debate, which was weighted heavily here. However, the HR/Culture Agent's evidence on communication and leadership was not directly challenged and still supports a moderate positive signal, which offsets some of the technical concerns. This is not an average of the four scores -- the technical credibility issue was given more weight because it was corroborated by the candidate's own admission in the transcript.",
  "strengths": ["Clear communicator", "Some leadership experience"],
  "concerns": ["Overstated technical skills, particularly around MongoDB and ML experience"],
  "unresolved_disagreements": ["Whether the leadership claim is fully trustworthy given other exaggerations found"]
}"""

    return '{"error": "mock response not defined for this prompt"}'