
**setup**


https://github.com/user-attachments/assets/2540540f-357f-4d5c-b456-70fc438149f3

# StackDecide

**Should you use Zustand or Redux? SQLite or Postgres? REST or WebSockets? StackDecide researches it, scores the options, and tells you — with real-time information, not stale training data — before you ask your AI coding agent to just pick one for you.**

StackDecide is a VS Code extension + agentic backend that helps you **choose libraries, frameworks, and architecture patterns** for your project. Paste in a single question, or a whole multi-part spec describing what you're building — StackDecide extracts every distinct technical decision hiding inside it, researches each one on the live web, scores the realistic options against your actual codebase, and hands you back a clear, comparable result — plus a ready-to-paste prompt to hand the decisions off to Codex, Antigravity, or any AI coding agent.

> Built for the **AI Agents: Intensive Vibe Coding Capstone Project** (Kaggle x Google) — Concierge Agents track.

---

## The Problem

"Vibe coding" — describing what you want in natural language and letting an AI agent write the code — is incredibly productive. But it has a quiet failure mode: **the AI silently picks your libraries and architecture for you, and you rarely find out it had other options.**

Tell an AI coding agent "add state management to my React app" and it will just pick Zustand, or Redux, or Context API — whichever it leans toward — and start writing code. Ask it to "store this data somewhere" and it picks SQLite, or Postgres, or a JSON file, without telling you:

- **What else it considered** (did it even compare alternatives, or just default to the first one it knows well?)
- **Why this one** (is there an actual reason, or is it just statistically common in its training data?)
- **Whether that reason still holds today** (a library that was the obvious choice two years ago may be poorly maintained now — the AI's training data doesn't know that)
- **Whether it actually fits *your* project** (your existing stack, your team size, your free-tier budget — context the AI usually isn't given)

Over time, this produces codebases full of library and architecture choices nobody actually made on purpose — including the developer who's supposed to own those decisions.

## The Solution

StackDecide sits between you and your coding agent. Before you ask Codex/Antigravity/etc. to implement something architecturally significant, you ask StackDecide first — whether that's one specific question or a whole project spec. It:

1. **Extracts every decision hiding in your prompt.** A one-line question ("Zustand or Redux?") is treated as one decision. A full spec ("build a todo app with auth, real-time sync, and file upload") gets broken down into each distinct technical choice it implies — auth method, sync mechanism, storage strategy — automatically.
2. **Researches each one in real time** — live web search, not the LLM's stale training data, so the comparison reflects current library trends and maintenance status, not what was popular when the model was trained.
3. **Scores the realistic options** for each decision — performance, maintainability, cost/free-tier feasibility, and fit with *your actual project* — in a clear side-by-side table, with a one-line "why this over the alternative" for the winner.
4. **Knows your real project** — it auto-detects your actual stack (`package.json`, `requirements.txt`, file structure) rather than reasoning in the abstract, and is aware of monorepo-style sibling sub-projects.
5. **Remembers past decisions** in this project, so it stays consistent instead of contradicting itself query to query.
6. **Knows when a question doesn't apply** — if you ask a frontend question against a pure backend context (or vice versa), it says so explicitly instead of hallucinating a fake answer that sounds confident but means nothing. If *everything* you asked turns out to be a mismatch, it tells you that plainly instead of pretending it has a recommendation.
7. **Hands off cleanly** — one click appends a clean "Consider this when implementing" block to your *original* prompt — untouched, just annotated with the chosen tech and why — so the decisions you just made become the foundation for the implementation, instead of getting re-litigated or ignored.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  VS Code Extension (TypeScript)                                              │
│  ┌──────────────────────┐          ┌────────────────────────────────┐        │
│  │  Analysis View       │          │  Settings View                 │        │
│  │  - query input       │          │  - LLM provider (BYOK)         │        │
│  │  - score tables      │          │  - LLM API key                 │        │
│  │  - mismatch banner   │          │  - Tavily API key              │        │
│  │  - copy-to-agent     │          │  (independently editable)      │        │
│  └──────────────────────┘          └────────────────────────────────┘        │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ REST (localhost)
┌───────────────────────────────▼──────────────────────────────────────────────┐
│  FastAPI Backend (Python)                                                    │
│                                                                              │
│  0. Context Merge + Memory Load                                              │
│     auto-detected project stack + manual override                            │
│     + sibling sub-project detection + past decisions                         │
│                                                                              │
│  CALL 1 — Extraction + Query Planning (single LLM call)                      │
│     Reads the prompt + project context + memory → identifies                 │
│     every distinct decision, flags any that don't fit the project            │
│     context up front, generates exactly 2 search queries per                 │
│     decision that needs research                                             │
│                                                                              │
│  ── guard: >10 decisions found → requires explicit user approval ──          │
│  ── before continuing (proceed_anyway) ──                                    │
│                                                                              │
│  WEB RESEARCH (Tavily API, no LLM call)                                      │
│     Concurrent search across all decisions' queries; mismatched              │
│     decisions skip research entirely                                         │
│                                                                              │
│  CALL 2 — Scoring (one or a few batched LLM calls)                           │
│     Scores every realistic option per decision across 4 dimensions           │
│     (performance, maintainability, cost, project fit) → picks a winner       │
│     per decision. Large decision sets are split into small concurrent        │
│     batches to stay within free-tier token limits — most requests            │
│     still complete in exactly one call.                                      │
│                                                                              │
│  CALL 3 — Annotated Prompt (pure string templating, zero LLM calls)          │
│     Appends a "Consider this when implementing" block to the                 │
│     *original, untouched* prompt — or, if nothing was actionable,            │
│     a clarification request instead                                          │
│                                                                              │
│  Memory: one record per decision topic → .stackdecide/memory.json            │
│  LLM Providers (BYOK): Gemini · Claude · GPT · Grok · Groq · OpenRouter      │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Why this counts as agentic, not just "a chatbot with extra steps"

- **Autonomous decomposition**: the system doesn't wait to be told what's being decided — it reads an open-ended prompt and figures out, on its own, how many distinct technical decisions are actually in there.
- **Tool use**: live web search (Tavily) and filesystem inspection are invoked as tools the agent uses to ground its reasoning in current, real information rather than relying solely on the LLM's internal knowledge.
- **Self-aware scope management**: the >10-decision approval guard and the per-batch token budgeting are the system reasoning about its own limits and adapting its own execution plan, not just running a fixed script.
- **Calibrated honesty**: when the project context doesn't match the question — for one decision, or for all of them — the system says so explicitly instead of producing a fluent but meaningless answer. This was deliberately built and tested as a first-class behavior, not an afterthought.


## Tech Stack

| Layer | Technology |
|---|---|
| Extension frontend | TypeScript, VS Code Webview API |
| Backend | Python, FastAPI, httpx (async) |
| Search/research | Tavily Search API |
| LLM access | BYOK — Gemini, Claude, GPT, Grok, Groq, or OpenRouter (user supplies their own key) |
| Memory | Local JSON file, per-project (`.stackdecide/memory.json`) |
| Concurrency | `asyncio.gather` for parallel search and parallel scoring batches |

---

## Setup

### Prerequisites
- Python 3.9+
- Node.js + npm
- VS Code
- A free [Tavily](https://tavily.com) API key (1,000 free requests/month, no card required)
- An API key for at least one supported LLM provider (Gemini's free tier via [Google AI Studio](https://aistudio.google.com), or Groq's free tier, are the easiest to start with)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# LLM provider/key and Tavily key can be set here, OR later via the
# extension's Settings panel (recommended — no file editing needed)

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
3. Click the gear icon → select your LLM provider → paste your LLM API key → paste your Tavily API key → **Save Settings**.
4. Type a decision query — anything from a one-line question to a full project spec — and click **Analyze Decision**.
5. Review the score table(s) for each decision found, and click **Copy Annotated Prompt** to hand the decisions off to your coding agent of choice.

---

## Security Notes

- No API keys are hardcoded anywhere in this codebase. Keys are supplied at runtime via `.env` (gitignored) or the extension's Settings panel (held in backend memory only, never written to disk or returned in API responses).
- `GET /settings` returns only configuration status (e.g. `{"provider": ..., "configured": bool, "tavily_configured": bool}`) — raw keys are never echoed back to the client.
- Settings updates are partial — saving one key (e.g. just the Tavily key) never clears or overwrites a previously-saved, unrelated key (e.g. the LLM key).
- `.gitignore` excludes `.env`, `.stackdecide/` (per-project memory, may contain project-specific details the user may not want committed), `node_modules/`, `__pycache__/`, and `*.vsix`.

---

## Known Limitations

- **Sibling-project detection** (used for the context-mismatch check) currently scans from the given workspace root downward — if VS Code is opened directly inside a sub-folder of a monorepo (e.g. just `backend/`, not the repo root), it won't see a sibling `frontend/` folder one level up.
- **Free-tier LLM token limits** mean very large decision sets (10+ decisions in one request) are automatically split into smaller concurrent scoring batches rather than one giant call — this keeps the system from crashing, but on a fully free-tier setup, occasional individual batches can still get rate-limited under heavy concurrent load; these are surfaced as explicit "please retry this decision" results rather than silently dropped or fabricated.

## Future Goals

- **GitHub maintenance-health signal** — beyond live web search, factor in a library's actual repository activity (recent commits, issue-response time, release cadence) as an interpreted "is this still healthy?" signal rather than raw star counts, to catch quietly-abandoned libraries that still show up as popular in search results.
- **CLI version** — a terminal-only mode for developers who live outside VS Code, or who want to call StackDecide from any IDE's integrated terminal or a CI step.
- **Team / shared-memory mode** — let multiple developers on the same project share a single `.stackdecide` decision history (with appropriate access control), so architectural decisions stay consistent across a whole team, not just a single contributor's local memory.
- **Visual decision-dependency graph** — many real decisions aren't independent (choosing a database affects what ORM makes sense, which affects deployment options); a graph view showing how the decisions extracted from a single prompt relate to and constrain each other, instead of just a flat list of scored tables.

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
│       ├── reasoning/        # extraction, scoring, annotated-prompt generation
│       ├── memory/            # per-project decision history + context builder
│       └── context/            # auto project-context scanner
└── README.md
```

---

## Built With

Built as part of Kaggle's *AI Agents: Intensive Vibe Coding* course, using an AI-assisted ("vibe coding") workflow itself — architecture and prompts were planned and reviewed iteratively, with implementation carried out by AI coding agents (Antigravity, with portions via Kimi) under close human review at every step. This included a full mid-build architectural refactor — replacing an early 6-LLM-call-per-decision reasoning loop with a leaner 2-call extraction-and-scoring engine — after the original design proved too rate-limit-fragile on free-tier APIs, and catching several real reasoning bugs along the way (such as an early version that recommended a "Python-compatible Zustand alternative" for a question that didn't apply to the project at all) before they shipped.
