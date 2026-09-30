# BRD Accelerator (Google AI Studio / Gemini)
1. `cp .env.example .env` and set `GEMINI_API_KEY` (aistudio.google.com/apikey) + `ADMIN_PASSWORD`
2. `npm install && npm start` → http://localhost:3000

Flow: Client brief → **Agent 1** (interviewer, loops until topic coverage ≥70% or MAX_ROUNDS) → JSON hand-off
(`schemaVersion, project, readiness, qa[]`) → **Agent 2** (BRD + tasks + assumptions) → server computes schedule/cost
from admin defaults (holidays per geography, utilisation, leave, contingency, rates) → user approves/edits assumptions,
changes defaults or gives feedback → orchestrator re-runs Agent 2 only.
Admin tab edits `data/defaults.json` (protected by `ADMIN_PASSWORD`).
