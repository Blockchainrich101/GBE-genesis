# GBE Genesis: local diagnostic milestone

Use the phase1-minimum-gie-core branch. The main branch is an architecture baseline.

This implementation starts a local web interface, checks storage readiness and processes one validated diagnostic request into SQLite. It also supports supervised drafting with an installed local Ollama model. Autonomous tool execution, research, email, recursive improvement and the complete GIE architecture remain unimplemented.

## Windows setup

Install Python 3.12 or newer. Extract the repository ZIP before running anything. In a terminal opened in the extracted repository directory:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m app
```

Open http://127.0.0.1:8000 in a browser. The server stays in the terminal; Ctrl+C stops it. After setup, double-click start-windows.cmd. It keeps the window open when startup fails.

## Linux/macOS

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m app
```

## Diagnostics and limitations

- GET /health/live checks the process; GET /health/ready checks the local database table.
- POST /api/requests accepts only {"action":"diagnose","text":"Check startup"}. Blank text, oversized input and other actions are rejected.
- The interface stops waiting after 10 seconds and displays errors. A timed-out request may already have been saved; retries create separate diagnostic records.
- Data is stored in ~/.gbe-genesis/requests.sqlite3. Set GBE_DB_PATH before startup to override it. Text is stored locally without application-level encryption; avoid sensitive data.
- Storage initialization errors fail startup with an actionable log. Runtime storage failures return HTTP 503.
- Port 8000 already occupied: stop the conflicting server, then restart.
- No authentication is included. The supported launcher binds only to 127.0.0.1; do not expose this prototype to a network.
- Installation needs internet access. Once installed, this local diagnostic works offline.
- Dependency ranges remain flexible; no cross-platform lockfile is claimed.

## Verification

Run python -m pytest inside the installed environment. Tests cover readiness, persistent completion, rejected input and storage failures. CI runs these checks on Linux and Windows.


## Offline drafting agent (Windows)

Install Ollama from https://ollama.com/download/windows. Before starting Ollama, set the user environment variable OLLAMA_NO_CLOUD=1 and fully quit/restart Ollama. This disables cloud models and web search (https://docs.ollama.com/faq). The app itself connects only to 127.0.0.1:11434 with no proxy, redirect or cloud fallback. Server-side cloud disabling is required as model-name checks alone cannot verify custom aliases.

In PowerShell, download a modest example model (hardware suitability and speed must be checked on your computer):

```powershell
ollama pull qwen2.5:3b
$env:GBE_LOCAL_MODEL="qwen2.5:3b"
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m app
```

Open http://127.0.0.1:8000, select Offline agent draft, enter a task and run it. Example: Draft a five-step manual startup test plan for GBE. The output is marked REVIEW REQUIRED and saved locally. The model download needs internet; inference can run offline afterward. Model reference: https://ollama.com/library/qwen2.5:3b.

The selected model variable above applies to this PowerShell session. To use the double-click launcher, also set GBE_LOCAL_MODEL in Windows user environment variables and reopen the launcher.

Each request is user initiated. The agent has no tools, file access, email, browser or shell capability. Draft text is not executed. Model requests have a 90-second overall deadline and a 1024-token output limit; only one draft runs per application process. Run a single server worker. A timed-out model may continue computing inside Ollama briefly; this app does not claim to terminate Ollama's process. Health readiness reports the diagnostic/storage service, not model availability. Missing model configuration is reported when a draft is requested.

Verification: 14 tests pass with mocked model responses, including missing configuration, rejected cloud model names, connection failures, timeouts, invalid responses and saved drafts. Real model inference and Windows startup have not been verified here. Earlier CI attempts stopped before executing test steps.
