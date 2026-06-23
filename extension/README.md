# StackDecide

**StackDecide** is an AI-powered tech stack decision tool that sits inside your VS Code. 

Should you use Zustand or Redux? SQLite or Postgres? REST or WebSockets? StackDecide researches it, scores the options, and tells you — with real-time information, not stale training data — before you ask your AI coding agent to just pick one for you.

## Features

- **Extract Decisions:** Provide an entire project spec or a single question. StackDecide breaks it down into individual technical decisions.
- **Real-Time Research:** Uses Tavily search to pull live documentation, issues, and up-to-date data for each candidate technology.
- **Context-Aware Scoring:** It reads your workspace context (`package.json`, `requirements.txt`, etc.) to score decisions against your project's *actual* stack for performance, maintainability, cost, and fit.
- **Annotated Prompt Generation:** Copies a structured "decision output" block that you can append to your prompt for your coding agent (like Codex or Antigravity) to ensure it implements the right tech.

## Getting Started

1. Open a workspace or folder in VS Code.
2. Run the command **StackDecide: Analyze Decision** from the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`).
3. If this is your first time, the extension will automatically set up its local Python backend in the background. (Python 3.9+ is required on your system).
4. Click the gear icon in the StackDecide panel to set up your LLM Provider API Key and your [Tavily](https://tavily.com) Search API Key.
5. Enter your decision request and hit **Analyze Decision**!

## Requirements

- Python 3.9 or newer must be installed on your machine and available in your PATH.
- An API key for an LLM provider (e.g., Gemini, Claude, Groq, Grok).
- A free [Tavily API key](https://tavily.com) for real-time web research.

## How it works under the hood

StackDecide uses a local FastAPI backend to execute reasoning logic. When you install the extension, the Python files are included. On first run, the extension automatically creates a virtual environment and installs the required packages, and then spawns the server in the background. When you close the extension, the server stops automatically.
