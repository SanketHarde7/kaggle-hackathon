# StackDecide

**Stop letting your AI coding agent make silent architecture decisions for you.**

StackDecide is a VS Code extension + agentic backend that researches, reasons about, and explains technical decisions — *before* you hand them off to an AI coding agent (like Antigravity,Codex, or any other) — so you understand **what** is being chosen and **why**, with real-time information instead of stale training data.

> Built for the **AI Agents: Intensive Vibe Coding Capstone Project** (Kaggle x Google) — Concierge Agents track.

---

## The Problem

"Vibe coding" — describing what you want in natural language and letting an AI agent write the code — is incredibly productive. But it has a quiet failure mode: **the AI silently picks the architecture for you.**

Ask an AI coding agent to "add state management" and it picks a library. Ask it to "add caching" and it picks a strategy. It rarely tells you:
- What alternatives existed
- Why it picked this one over the others
- Whether its choice is still the *current* best practice, or just what was popular when it was trained
- Whether the choice even fits the project you're actually building

Over time, this produces codebases full of decisions nobody actually made on purpose — including the developer who's supposed to own the architecture.

## The Solution

StackDecide sits between you and your coding agent. Before you ask Codex/Antigravity/etc. to implement something architecturally significant, you ask StackDecide first. It:

1. **Researches the decision in real time** — not from stale training data, but from live web search, so it reflects current library trends, maintenance status, and community sentiment.
2. **Reasons about it from four angles** — performance/scalability, maintainability, cost/free-tier feasibility, and fit with *your actual project* — and explicitly critiques its own first-draft answer before finalizing.
3. **Knows your real project** — it auto-detects your actual stack (`package.json`, `requirements.txt`, file structure) rather than reasoning in the abstract.
4. **Remembers past decisions** in this project, so it stays consistent instead of contradicting itself query to query.
5. **Knows when a question doesn't apply** — if you ask a frontend question against a pure backend context (or vice versa), it says so explicitly instead of hallucinating a fake answer that sounds confident but means nothing.
6. **Hands off cleanly** — one click copies a ready-to-paste, context-rich prompt for your coding agent, so the decision you just made becomes the foundation for the implementation, instead of getting re-litigated or ignored.

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│  VS Code Extension (TypeScript)                        │
│  ┌──────────────────┐        ┌──────────────────────┐  │
│  │  Analysis View    │        │  Settings View         │   
│  │  - query input    │        │  - provider dropdown   │   
│  │  - decision brief │        │    (BYOK)              │  
│  │  - copy-to-agent  │        │  - API key (masked)    │  
│  └──────────────────┘        └──────────────────────┘  │
└───────────────────────┬──────────────────────────────────┘
                        │ REST (localhost)
┌───────────────────────▼─────────────────────────────────────┐
│  FastAPI Backend (Python)                                   │
│                                                             │
│  1. Context Merge                                           │
│     auto-detected project stack + manual override           │
│     (detects monorepo sibling sub-projects)                 │
│                                                             │
│  2. Web Research (Tavily API)                               │
│     LLM plans 3-5 targeted search queries → concurrent      │
│     search → dedup + clean → structured findings            │
│                                                             │
│  3. Multi-Angle Self-Critique Reasoning (agentic loop)      │
│     Stage 1: initial draft                                  │
│     Stage 2: 4 concurrent critique passes                   │
│              (performance / maintainability / cost / fit)   │
│     Stage 3: synthesis — resolves disagreements, or flags   │
│              a context-domain mismatch instead of forcing one│
│                                                             │
│  4. Project Memory (.stackdecide/memory.json)               │
│     past decisions persist per-project; token-budgeted      │
│     context injection prioritizes topically related history │
│                                                             │
│  5. Prompt Generator                                        │
│     formats the final brief into a ready-to-paste agent prompt│
│     (or a clarification request, if a mismatch was flagged)│
│                                                             │
│  LLM Providers (BYOK): Gemini · Claude · GPT · Grok · Groq · OpenRouter|
└────────────────────────────────────────────────────────────────────────┘
```

### Why this counts as agentic, not just "a chatbot with extra steps"

- **Multi-stage autonomous reasoning**: the system plans its own research queries, critiques its own draft answer from independent angles, and synthesizes a final decision — without a human in the loop between steps.
- **Tool use**: live web search (Tavily) and filesystem inspection are used as tools the agent invokes to ground its reasoning in current, real information rather than relying solely on the LLM's internal knowledge.
- **Self-correction**: the four-angle critique stage exists specifically so the system can disagree with and revise its own first answer — this is reflection, not a single forward pass.
- **Calibrated honesty**: when the project context doesn't match the question, the system says so explicitly instead of producing a fluent but meaningless answer. This was deliberately built and tested as a first-class behavior, not an afterthought.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Extension frontend | TypeScript, VS Code Webview API |
| Backend | Python, FastAPI, httpx (async) |
| Search/research | Tavily Search API |
| LLM access | BYOK — Gemini, Claude, GPT, Grok, Groq, or OpenRouter (user supplies their own key) |
| Memory | Local JSON file, per-project (`.stackdecide/memory.json`) |
| Concurrency | `asyncio.gather` for parallel search and parallel critique passes |

---

## Setup

### Prerequisites
- Python 3.9+
- Node.js + npm
- VS Code
- A free [Tavily](https://tavily.com) API key (1,000 free requests/month, no card required)
- An API key for at least one supported LLM provider (Gemini's free tier via [Google AI Studio](https://aistudio.google.com) is the easiest to start with)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add: TAVILY_API_KEY=tvly-...
# (LLM provider/key can be set here OR later via the extension's Settings panel)

uvicorn app.main:app --reload
```
Backend runs at `http://localhost:8000`. Confirm it's healthy: `GET http://localhost:8000/health` → `{"status": "ok"}`.

### Extension

```bash
cd extension
npm install
npm run compile
```
Open the `extension/` folder in VS Code and press `F5` to launch an Extension Development Host window.

### First run

1. In the Extension Development Host, open the project folder you want decisions about.
2. Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) → **StackDecide: Analyze Decision**.
3. Click the gear icon → select your LLM provider → paste your API key → **Save Settings**.
4. Type a decision query (e.g. *"Should I use Zustand or Redux for state management?"*) → **Analyze Decision**.
5. Review the brief, expand the critique angles, and click **Copy Codex Prompt** to hand the decision off to your coding agent of choice.

---

## Security Notes

- No API keys are hardcoded anywhere in this codebase. Keys are supplied at runtime via `.env` (gitignored) or the extension's Settings panel (held in backend memory only, never written to disk or returned in API responses).
- `GET /settings` returns only `{"provider": ..., "configured": bool}` — the raw key is never echoed back to the client.
- `.gitignore` excludes `.env`, `.stackdecide/` (per-project memory, may contain project-specific details the user may not want committed), `node_modules/`, `__pycache__/`, and `*.vsix`.

---

## Known Limitations / Future Work

- **Sibling-project detection** (used for the context-mismatch check) currently scans from the given workspace root downward — if VS Code is opened directly inside a sub-folder of a monorepo (e.g. just `backend/`, not the repo root), it won't see a sibling `frontend/` folder one level up. A future version would walk upward as well as downward.
- **GitHub repository health signals** (maintenance activity, star trends) were deliberately descoped from the research step for this submission to keep the research pipeline simple and reliable within the timeline; web search currently covers the "is this still relevant" question well enough on its own.
- **Multi-model cross-verification**: the reasoning loop currently uses a single configured LLM provider with a 4-angle self-critique structure. A natural extension would let the synthesis stage optionally draw on a second provider for true cross-model consensus, for users who configure more than one key.
- Antigravity-specific extension support (in addition to VS Code) is planned as a follow-up.

---

## Project Structure

```
stackdecide/
├── extension/              # VS Code extension (TypeScript)
│   └── src/
│       ├── extension.ts    # command registration, activation
│       ├── panel.ts        # webview lifecycle, message bridge
│       └── ui.ts           # webview HTML/CSS/JS (Analysis + Settings views)
├── backend/                 # FastAPI backend (Python)
│   └── app/
│       ├── main.py
│       ├── config.py        # settings, BYOK runtime/env precedence
│       ├── routes/          # /analyze, /settings, /health
│       ├── providers/       # Gemini, Claude, GPT, Grok, Groq, OpenRouter
│       ├── research/        # query planning, Tavily search, cleaning, orchestration
│       ├── reasoning/        # 4-angle self-critique loop, Codex prompt generator
│       ├── memory/            # per-project decision history + context builder
│       └── context/            # auto project-context scanner
└── README.md
```

---

## Built With

Built as part of Kaggle's *AI Agents: Intensive Vibe Coding* course, using an AI-assisted ("vibe coding") workflow itself — architecture and prompts were planned and reviewed iteratively, with implementation carried out by AI coding agents (Antigravity, with portions via Kimi) under close human review at every step, including catching and fixing several real reasoning bugs (such as an early version that recommended a "Python-compatible Zustand alternative" for a question that didn't apply to the project at all) before they shipped.