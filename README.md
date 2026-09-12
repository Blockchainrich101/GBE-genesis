# GBE Genesis: local diagnostic milestone

Use the phase1-minimum-gie-core branch. The main branch is an architecture baseline.

This implementation starts a local web interface, checks storage readiness and processes one validated diagnostic request into SQLite. It does not implement AI reasoning, autonomous agents, research, email, recursive improvement or the complete GIE architecture.

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
