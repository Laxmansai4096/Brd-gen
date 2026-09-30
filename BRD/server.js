import 'dotenv/config';
import express from 'express';
import fs from 'fs';
import { randomUUID } from 'crypto';
import { GoogleGenAI } from '@google/genai';

const { GEMINI_API_KEY, GEMINI_MODEL = 'gemini-2.5-flash', ADMIN_PASSWORD, PORT = 3000 } = process.env;
const MAX_ROUNDS = +(process.env.MAX_ROUNDS || 5);
if (!GEMINI_API_KEY) console.warn('! GEMINI_API_KEY missing in .env');
const ai = new GoogleGenAI({ apiKey: GEMINI_API_KEY });
const DEF = fs.existsSync('data/defaults.json') ? 'data/defaults.json' : 'defaults.json';
const getDefaults = () => JSON.parse(fs.readFileSync(DEF, 'utf8'));
const sessions = new Map();
const app = express();
app.use(express.json({ limit: '1mb' }));
app.use(express.static('public'));
app.use(express.static('.'));

const llm = async (system, payload) => {
  const r = await ai.models.generateContent({
    model: GEMINI_MODEL, contents: JSON.stringify(payload),
    config: { systemInstruction: system, responseMimeType: 'application/json', temperature: 0.3 } });
  return JSON.parse(r.text);
};

// ---------- AGENT 1: Interviewer ----------
const TOPICS = ['objective','users_personas','scope_in_out','functional_requirements','non_functional','integrations','data_sources','tech_platform','geography_location','team_start_date_duration','budget','compliance_security','success_metrics','risks_constraints'];
const A1 = `You are a senior Business Analyst interviewing a client to write a BRD.
Required topics: ${TOPICS.join(', ')}.
Given the project brief and the Q&A so far, score each topic's clarity 0-100 and decide readiness.
Rules: ready=true only when every topic >=70 or round limit reached (isLastRound=true forces ready=true).
If not ready, ask at most 5 NEW, specific, non-repeated questions targeting the weakest topics. Never re-ask answered questions.
Return JSON only: {"ready":bool,"coverage":{"topic":number},"questions":[{"id":"Q<n>","topic":"","text":""}],"note":"one line"}`;

const runInterviewer = async (s) => {
  const isLastRound = s.round >= MAX_ROUNDS;
  const out = await llm(A1, { brief: s.brief, qa: s.qa.map(({ id, topic, question, answer }) => ({ id, topic, question, answer })), round: s.round, isLastRound, nextQuestionNumber: s.qa.length + s.pending.length + 1 });
  s.coverage = out.coverage || {};
  if (out.ready || isLastRound || !out.questions?.length) { s.status = 'ready'; s.pending = []; }
  else { s.status = 'asking'; s.pending = out.questions; s.round++; }
  s.note = out.note || '';
};

// exact hand-off contract between Agent 1 and Agent 2
const buildHandoff = (s) => ({ schemaVersion: '1.0', project: s.brief, readiness: s.coverage,
  qa: s.qa.map(({ id, topic, question, answer }) => ({ id, topic, question, answer })) });

// ---------- Deterministic calendar + estimate ----------
const iso = (d) => d.toISOString().slice(0, 10);
const addWorkingDays = (start, n, holidays, wdpw) => {
  const hol = new Set(holidays.map((h) => h.date)); const d = new Date(start + 'T00:00:00Z'); let left = Math.max(1, Math.ceil(n));
  const offDay = (x) => (wdpw >= 5 ? [0, 6] : [0]).includes(x.getUTCDay()) || hol.has(iso(x));
  while (offDay(d)) d.setUTCDate(d.getUTCDate() + 1);
  while (--left > 0) { do d.setUTCDate(d.getUTCDate() + 1); while (offDay(d)); }
  return iso(d);
};
const computeEstimate = (brd, eff) => {
  const hol = (eff.geographies[eff.geography] || { holidays: [] }).holidays;
  const availability = eff.utilisation * (1 - eff.leaveDaysPerYear / (52 * eff.workingDaysPerWeek));
  let cursor = eff.startDate, total = 0, cost = 0;
  const phases = (brd.phases || []).map((p) => {
    const tasks = (brd.tasks || []).filter((t) => t.phase === p.name);
    const effort = tasks.reduce((a, t) => a + (+t.days || 0), 0) * (1 + eff.contingencyPct / 100);
    const elapsed = Math.max(1, Math.ceil(effort / (Math.max(1, p.teamSize) * availability)));
    const start = addWorkingDays(cursor, 1, hol, eff.workingDaysPerWeek);
    const end = addWorkingDays(start, elapsed, hol, eff.workingDaysPerWeek);
    cursor = end; total += effort;
    tasks.forEach((t) => (cost += t.days * (1 + eff.contingencyPct / 100) * (eff.rates[t.role] || 0)));
    return { name: p.name, teamSize: p.teamSize, effortDays: +effort.toFixed(1), workingDays: elapsed, start, end };
  });
  return { phases, totalEffortDays: +total.toFixed(1), endDate: cursor, cost: Math.round(cost), currency: eff.currency, availability: +availability.toFixed(3), holidaysUsed: hol };
};

// ---------- AGENT 2: BRD writer / planner ----------
const A2 = `You are a BRD author and delivery planner. Input: hand-off Q&A JSON, effective planning defaults (calendar, geography, utilisation, rates), optional user feedback, and user assumption decisions.
Produce a complete BRD. Do NOT compute dates/totals - only tasks with person-days; the system computes schedule and cost.
Every assumption must be tagged source: "client" (from an answer, cite QIDs in ref), "default" (from planning defaults) or "inferred".
If feedback or rejected/edited assumptions are given, revise the plan accordingly and say what changed in "changeLog".
Use only role names present in defaults.rates. Return JSON only:
{"sections":[{"title":"","content":"markdown"}],"assumptions":[{"id":"A1","text":"","source":"client|default|inferred","ref":""}],"phases":[{"name":"","teamSize":number}],"tasks":[{"id":"T1","phase":"<phase name>","task":"","role":"","days":number}],"risks":[{"risk":"","mitigation":""}],"changeLog":""}
Sections required: Executive Summary, Business Objectives, Scope (In/Out), Stakeholders & Personas, Functional Requirements, Non-Functional Requirements, Integrations & Data, Technical Approach, Security & Compliance, Success Metrics, Delivery Approach, Open Questions.`;

const generate = async (s, { feedback = '', overrides = {}, assumptionDecisions = [] } = {}) => {
  s.overrides = { ...s.overrides, ...overrides };
  const eff = { ...getDefaults(), ...s.overrides };
  if (feedback) s.feedback.push(feedback);
  const brd = await llm(A2, { handoff: buildHandoff(s), defaults: { ...eff, geographies: undefined, holidays: (eff.geographies[eff.geography] || {}).holidays }, feedbackHistory: s.feedback, assumptionDecisions, previousBrd: s.brd || null });
  s.brd = brd; s.estimate = computeEstimate(brd, eff); s.effective = { geography: eff.geography, startDate: eff.startDate, utilisation: eff.utilisation, contingencyPct: eff.contingencyPct, leaveDaysPerYear: eff.leaveDaysPerYear };
  s.versions++;
};

const view = (s) => ({ id: s.id, status: s.status, round: s.round, coverage: s.coverage, note: s.note, questions: s.pending, qaCount: s.qa.length, brd: s.brd, estimate: s.estimate, effective: s.effective, versions: s.versions, handoff: s.status === 'ready' ? buildHandoff(s) : undefined });
const wrap = (fn) => (req, res) => fn(req, res).catch((e) => { console.error(e); res.status(500).json({ error: e.message }); });
const need = (req, res) => { const s = sessions.get(req.params.id); if (!s) res.status(404).json({ error: 'session not found' }); return s; };

// ---------- Orchestrator routes ----------
app.post('/api/sessions', wrap(async (req, res) => {
  const { name, client, description } = req.body;
  if (!description) return res.status(400).json({ error: 'description required' });
  const s = { id: randomUUID(), brief: { name, client, description }, qa: [], pending: [], round: 1, coverage: {}, overrides: {}, feedback: [], versions: 0 };
  sessions.set(s.id, s); await runInterviewer(s); res.json(view(s));
}));

app.post('/api/sessions/:id/answers', wrap(async (req, res) => {
  const s = need(req, res); if (!s) return;
  s.pending.forEach((q) => s.qa.push({ ...q, question: q.text, answer: (req.body.answers?.[q.id] || 'Not answered').trim() }));
  s.pending = []; await runInterviewer(s);
  if (s.status === 'ready') await generate(s);       // Agent 1 satisfied -> hand off to Agent 2
  res.json(view(s));
}));

// user rejects plan / edits defaults -> orchestrator re-runs Agent 2 only
app.post('/api/sessions/:id/regenerate', wrap(async (req, res) => {
  const s = need(req, res); if (!s) return;
  await generate(s, req.body); res.json(view(s));
}));

// ---------- Admin-managed defaults ----------
const admin = (req, res, next) => (req.get('x-admin-key') === ADMIN_PASSWORD && ADMIN_PASSWORD ? next() : res.status(401).json({ error: 'admin key invalid' }));
app.get('/api/defaults', (_q, res) => res.json(getDefaults()));
app.put('/api/defaults', admin, (req, res) => {
  const d = req.body; if (!d?.geographies || !d?.rates) return res.status(400).json({ error: 'invalid defaults' });
  fs.writeFileSync(DEF, JSON.stringify(d, null, 2)); res.json({ ok: true });
});

app.listen(PORT, () => console.log(`BRD accelerator on http://localhost:${PORT}`));
