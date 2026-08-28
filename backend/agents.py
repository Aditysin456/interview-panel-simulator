"""
agents.py
Defines the system prompts and call logic for every agent in the panel.

IMPORTANT DESIGN RULE (per the challenge spec):
Each of the 4 independent agents is called in ISOLATION during Step 1 —
none of them see each other's opinions. They only see the shared
candidate profile. This file enforces that by giving each agent its
own function with its own isolated API call.
"""

import json

from llm_client import call_llm

# ---------------------------------------------------------------------
# STEP 0: CANDIDATE PROFILE BUILDER
# ---------------------------------------------------------------------

PROFILE_BUILDER_PROMPT = """You are the Candidate Profile Builder for an interview panel system.

You will receive a candidate's RESUME text and an INTERVIEW TRANSCRIPT text.
Extract a structured, factual profile that all panel agents will use.

Rules:
- Only extract what is actually stated. Do not invent skills or claims.
- Preserve important sentences from the transcript VERBATIM in
  "transcript_excerpts" so agents can quote them later as evidence.
- "claims" should capture things the candidate asserted about themselves
  (e.g. "led a team of 5", "3 years of experience with X") so the Skeptic
  Agent can later check them against the transcript.

Output ONLY valid JSON, no markdown, no commentary, in this exact shape:
{
  "skills": ["..."],
  "experience": [
    {"role": "...", "company": "...", "duration": "...", "highlights": ["..."]}
  ],
  "claims": ["..."],
  "transcript_excerpts": ["..."]
}
"""


def build_profile(resume_text: str, transcript_text: str) -> dict:
    user_message = (
        f"RESUME:\n{resume_text}\n\n"
        f"TRANSCRIPT:\n{transcript_text}\n\n"
        "Extract the structured candidate profile now."
    )
    raw = call_llm(system=PROFILE_BUILDER_PROMPT, user=user_message, max_tokens=2500)
    return _safe_json(raw, fallback={
        "skills": [], "experience": [], "claims": [], "transcript_excerpts": []
    })


# ---------------------------------------------------------------------
# STEP 1: FOUR INDEPENDENT AGENTS (isolated calls, no cross-visibility)
# ---------------------------------------------------------------------

AGENT_PROMPTS = {
    "technical": """You are the Technical Agent on an interview panel.
Your ONLY job is to evaluate the candidate's technical skill and depth,
based on the candidate profile you are given.

Rules:
- You must back your opinion with at least one direct quote or fact taken
  from the profile's transcript_excerpts, experience, or claims.
- Do not comment on communication, culture fit, or hiring decisions —
  that is not your job.
- Be honest: if evidence is thin, say so and lower your confidence.

Output ONLY valid JSON, no markdown, in this exact shape:
{"agent": "technical", "opinion": "...", "confidence": 0-100, "evidence": ["...", "..."]}
""",

    "hr_culture": """You are the HR/Culture Agent on an interview panel.
Your ONLY job is to evaluate communication clarity, teamwork signals,
and honesty/consistency of tone, based on the candidate profile you are given.

Rules:
- You must back your opinion with at least one direct quote or fact taken
  from the profile's transcript_excerpts, experience, or claims.
- Do not comment on technical depth or the final hiring decision —
  that is not your job.
- Be honest: if evidence is thin, say so and lower your confidence.

Output ONLY valid JSON, no markdown, in this exact shape:
{"agent": "hr_culture", "opinion": "...", "confidence": 0-100, "evidence": ["...", "..."]}
""",

    "hiring_manager": """You are the Hiring Manager Agent on an interview panel.
Your ONLY job is to judge whether this candidate is worth hiring for the
role overall, based on the candidate profile you are given.

Rules:
- You must back your opinion with at least one direct quote or fact taken
  from the profile's transcript_excerpts, experience, or claims.
- Take a holistic view (this is different from the Technical or HR agents),
  but you must still cite evidence, not just gut feeling.
- Be honest: if evidence is thin, say so and lower your confidence.

Output ONLY valid JSON, no markdown, in this exact shape:
{"agent": "hiring_manager", "opinion": "...", "confidence": 0-100, "evidence": ["...", "..."]}
""",

    "skeptic": """You are the Skeptic Agent on an interview panel.
Your ONLY job is to hunt for contradictions, exaggerations, or vague
non-answers in the candidate profile you are given.

Rules:
- You must quote or reference a SPECIFIC line from transcript_excerpts,
  experience, or claims for every concern you raise. Never invent a concern
  with no evidence.
- If you genuinely find nothing suspicious, say so explicitly and explain
  briefly why the candidate's claims held up under scrutiny.
- Do not soften your judgment to be polite — your job is to stress-test.

Output ONLY valid JSON, no markdown, in this exact shape:
{"agent": "skeptic", "opinion": "...", "confidence": 0-100, "evidence": ["...", "..."]}
""",
}


def run_independent_agent(agent_key: str, profile: dict) -> dict:
    """
    Calls ONE agent in isolation. This function must never be given
    other agents' opinions — that is what makes Step 1 genuinely
    independent, per the challenge rule.

    Includes an internal safety-net retry: if the call comes back empty
    or fails to parse (e.g. a transient rate-limit blip), it retries up
    to 2 extra times before falling back, since this has been observed
    to happen intermittently to a random single agent.
    """
    system_prompt = AGENT_PROMPTS[agent_key]
    user_message = (
        "CANDIDATE PROFILE (JSON):\n"
        f"{json.dumps(profile, indent=2)}\n\n"
        "Give your independent opinion now, in the required JSON format."
    )
    fallback = {
        "agent": agent_key, "opinion": "Could not generate opinion.",
        "confidence": 0, "evidence": []
    }
    for extra_attempt in range(3):
        raw = call_llm(system=system_prompt, user=user_message, max_tokens=1800)
        result = _safe_json(raw, fallback=None)
        if result is not None and result.get("opinion") not in (None, "", "Could not generate opinion."):
            return result
    return fallback


def run_all_independent_agents(profile: dict) -> dict:
    """Runs all 4 agents SEQUENTIALLY, each in its own isolated call.
    Sequential is safer on Groq free tier (avoids rate-limit 429s).
    Each agent still only ever sees the shared profile, never the
    other agents' opinions — isolation is preserved."""
    results = {}
    for key in AGENT_PROMPTS:
        results[key] = run_independent_agent(key, profile)
    return results


# ---------------------------------------------------------------------
# STEP 2: DEBATE
# ---------------------------------------------------------------------

DEBATE_PROMPT = """You are the Debate Orchestrator for an interview panel.

You will be given 4 independent agent opinions (technical, hr_culture,
hiring_manager, skeptic), each with their own confidence score and evidence.

Your job: simulate a REAL debate between these agents where they respond
DIRECTLY to each other, not just restate their own opinion again.

Hard requirements:
- Identify at least one genuine disagreement or tension between two agents
  (e.g. differing confidence, contradicting evidence, or opposing conclusions).
- Produce at least one exchange where Agent B explicitly reacts to Agent A's
  specific point — agreeing, disagreeing, or revising their own opinion
  because of it. This must reference the actual content of what was said,
  not be generic.
- If an agent revises its confidence because of the debate, include the new
  confidence value.
- List any disagreements that remain unresolved after the debate.

Output ONLY valid JSON, no markdown, in this exact shape:
{
  "exchanges": [
    {"from": "skeptic", "to": "technical", "message": "...", "type": "challenge"},
    {"from": "technical", "to": "skeptic", "message": "...", "type": "revise", "new_confidence": 65}
  ],
  "unresolved_conflicts": ["..."]
}

Valid values for "type": "challenge", "agree", "disagree", "revise".
"""


def run_debate(opinions: dict) -> dict:
    user_message = (
        "INDEPENDENT AGENT OPINIONS (JSON):\n"
        f"{json.dumps(opinions, indent=2)}\n\n"
        "Simulate the debate now, following all rules exactly."
    )
    raw = call_llm(system=DEBATE_PROMPT, user=user_message, max_tokens=2000)
    return _safe_json(raw, fallback={"exchanges": [], "unresolved_conflicts": []})


# ---------------------------------------------------------------------
# STEP 3: FINAL DECISION ENGINE (must NOT be a simple average)
# ---------------------------------------------------------------------

FINAL_DECISION_PROMPT = """You are the Final Decision Engine for an interview panel.

You will receive: the candidate profile, the 4 independent agent opinions,
and the debate transcript showing how agents challenged each other.

CRITICAL RULE: You must NOT simply average the 4 confidence scores. Instead:
1. Decide which agent's evidence is MOST relevant to whether this candidate
   should be hired, and explain why you weighted it that way.
2. Factor in any confidence revisions that happened during the debate.
3. Write out your weighting logic explicitly in "reasoning" — a reader
   should understand WHY you reached this recommendation, not just what
   the recommendation is.
4. Explicitly list any disagreement between agents that your decision did
   NOT fully resolve.

Output ONLY valid JSON, no markdown, in this exact shape:
{
  "recommendation": "Hire" or "No Hire" or "Hire with Reservations",
  "confidence": 0-100,
  "reasoning": "...",
  "strengths": ["..."],
  "concerns": ["..."],
  "unresolved_disagreements": ["..."]
}
"""


def run_final_decision(profile: dict, opinions: dict, debate: dict) -> dict:
    user_message = (
        "CANDIDATE PROFILE (JSON):\n"
        f"{json.dumps(profile, indent=2)}\n\n"
        "INDEPENDENT OPINIONS (JSON):\n"
        f"{json.dumps(opinions, indent=2)}\n\n"
        "DEBATE TRANSCRIPT (JSON):\n"
        f"{json.dumps(debate, indent=2)}\n\n"
        "Produce the final decision now, following all rules exactly."
    )
    raw = call_llm(system=FINAL_DECISION_PROMPT, user=user_message, max_tokens=2000)
    return _safe_json(raw, fallback={
        "recommendation": "Undetermined", "confidence": 0, "reasoning": "",
        "strengths": [], "concerns": [], "unresolved_disagreements": []
    })


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _safe_json(raw: str, fallback: dict) -> dict:
    """LLMs sometimes wrap JSON in markdown fences or add stray text.
    This strips that and parses safely, falling back if parsing fails."""
    if not raw:
        return fallback
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # try to find the first { ... last } as a last resort
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                pass
        return fallback