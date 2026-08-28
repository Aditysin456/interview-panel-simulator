// app.js — connects the UI to the FastAPI backend and renders each stage.

const BACKEND_URL = "http://localhost:8000";
document.getElementById("backend-url").textContent = BACKEND_URL;

const runBtn = document.getElementById("run-btn");
const sampleBtn = document.getElementById("sample-btn");
const statusMsg = document.getElementById("status-msg");
const resultsSection = document.getElementById("results");

const SAMPLE_RESUME = `John Doe
Backend Developer Intern at TechCorp (6 months)
Skills: Python, SQL, React, MongoDB, Machine Learning
Built REST APIs for internal tooling.`;

const SAMPLE_TRANSCRIPT = `Interviewer: Tell me about your experience.
Candidate: I led a team of 5 people during my internship.
Interviewer: What's your experience with machine learning?
Candidate: I have about 3 years of experience with machine learning, mostly self-taught.
Interviewer: You listed MongoDB as a skill, can you tell me more?
Candidate: Honestly I only used MongoDB for a couple of weeks on one project.`;

sampleBtn.addEventListener("click", () => {
  document.getElementById("resume").value = SAMPLE_RESUME;
  document.getElementById("transcript").value = SAMPLE_TRANSCRIPT;
});

runBtn.addEventListener("click", async () => {
  const resume_text = document.getElementById("resume").value.trim();
  const transcript_text = document.getElementById("transcript").value.trim();

  if (!resume_text || !transcript_text) {
    statusMsg.textContent = "Please provide both resume and transcript text.";
    return;
  }

  runBtn.disabled = true;
  statusMsg.textContent = "Running panel... profile → 4 agents → debate → final decision (this can take 20-40s on the real API, instant in mock mode)";
  resultsSection.classList.add("hidden");

  try {
    const response = await fetch(`${BACKEND_URL}/run-panel`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_text, transcript_text }),
    });

    if (!response.ok) {
      throw new Error(`Server responded with status ${response.status}`);
    }

    const data = await response.json();

    if (data.error) {
      statusMsg.textContent = `Error: ${data.error}`;
      return;
    }

    renderProfile(data.profile);
    renderOpinions(data.independent_opinions);
    renderDebate(data.debate);
    renderFinal(data.final_decision);

    resultsSection.classList.remove("hidden");
    statusMsg.textContent = "Panel complete.";
  } catch (err) {
    statusMsg.textContent = `Could not reach backend at ${BACKEND_URL}. Is it running? (${err.message})`;
  } finally {
    runBtn.disabled = false;
  }
});

function renderProfile(profile) {
  const el = document.getElementById("profile-output");
  el.innerHTML = `
    <p><strong>Skills:</strong> ${(profile.skills || []).join(", ") || "—"}</p>
    <p><strong>Experience:</strong></p>
    <ul>${(profile.experience || []).map(e =>
      `<li>${e.role || ""} at ${e.company || ""} (${e.duration || ""})</li>`
    ).join("") || "<li>—</li>"}</ul>
    <p><strong>Claims made by candidate:</strong></p>
    <ul>${(profile.claims || []).map(c => `<li>${escapeHtml(c)}</li>`).join("") || "<li>—</li>"}</ul>
  `;
}

function renderOpinions(opinions) {
  const el = document.getElementById("opinions-output");
  const labels = {
    technical: "Technical Agent",
    hr_culture: "HR / Culture Agent",
    hiring_manager: "Hiring Manager Agent",
    skeptic: "Skeptic Agent",
  };

  el.innerHTML = Object.keys(labels).map(key => {
    const op = opinions[key] || {};
    const confidence = op.confidence ?? 0;
    return `
      <div class="agent-card">
        <h3>${labels[key]}</h3>
        <p>${escapeHtml(op.opinion || "No opinion generated.")}</p>
        <div class="confidence-bar"><div class="confidence-fill" style="width:${confidence}%"></div></div>
        <div class="confidence-label" style="margin-bottom:8px;">Confidence: ${confidence}%</div>
        ${(op.evidence || []).map(q => `<div class="evidence-quote">"${escapeHtml(q)}"</div>`).join("")}
      </div>
    `;
  }).join("");
}

function renderDebate(debate) {
  const el = document.getElementById("debate-output");
  const exchanges = debate.exchanges || [];
  const unresolved = debate.unresolved_conflicts || [];

  el.innerHTML = `
    ${exchanges.map(ex => `
      <div class="exchange">
        <div class="exchange-arrow">${capitalize(ex.from)} → ${capitalize(ex.to)}</div>
        <div class="exchange-body">
          <span class="exchange-type type-${ex.type}">${ex.type}${ex.new_confidence !== undefined ? ` → ${ex.new_confidence}%` : ""}</span>
          <p>${escapeHtml(ex.message || "")}</p>
        </div>
      </div>
    `).join("") || "<p>No exchanges generated.</p>"}
    ${unresolved.length ? `
      <div class="unresolved-box">
        <strong>Unresolved after debate:</strong>
        <ul>${unresolved.map(u => `<li>${escapeHtml(u)}</li>`).join("")}</ul>
      </div>` : ""}
  `;
}

function renderFinal(final) {
  const el = document.getElementById("final-output");
  el.innerHTML = `
    <div class="recommendation">${escapeHtml(final.recommendation || "—")}</div>
    <div class="confidence-label">Confidence: ${final.confidence ?? 0}%</div>
    <div class="reasoning-box">${escapeHtml(final.reasoning || "")}</div>
    <div class="two-col">
      <div>
        <h4>Strengths</h4>
        <ul>${(final.strengths || []).map(s => `<li>${escapeHtml(s)}</li>`).join("") || "<li>—</li>"}</ul>
      </div>
      <div>
        <h4>Concerns</h4>
        <ul>${(final.concerns || []).map(c => `<li>${escapeHtml(c)}</li>`).join("") || "<li>—</li>"}</ul>
      </div>
    </div>
    ${(final.unresolved_disagreements || []).length ? `
      <div class="unresolved-box">
        <strong>Unresolved disagreements:</strong>
        <ul>${final.unresolved_disagreements.map(u => `<li>${escapeHtml(u)}</li>`).join("")}</ul>
      </div>` : ""}
  `;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function capitalize(s) {
  if (!s) return "";
  return s.charAt(0).toUpperCase() + s.slice(1);
}
