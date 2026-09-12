"""Local diagnostics and supervised offline drafting."""
import asyncio
import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator
from app.offline import draft

log = logging.getLogger(__name__)


class Request(BaseModel):
    action: str = Field(pattern="^diagnose$")
    text: str = Field(min_length=1, max_length=4000)

    @field_validator("text")
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("Enter a description.")
        return value.strip()


def create_app(db_path=None, model_transport=None):
    agent_lock = asyncio.Lock()
    path = Path(db_path or os.environ.get("GBE_DB_PATH", str(Path.home() / ".gbe-genesis" / "requests.sqlite3")))

    def connect():
        return sqlite3.connect(path, timeout=3)

    @asynccontextmanager
    async def lifespan(app):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with connect() as db:
                db.execute("CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, action TEXT NOT NULL, description TEXT NOT NULL, result TEXT NOT NULL)")
        except (OSError, sqlite3.Error):
            log.exception("Cannot initialize local database. Check GBE_DB_PATH and folder permissions.")
            raise RuntimeError("Database startup failed; check GBE_DB_PATH and folder permissions.") from None
        yield

    app = FastAPI(title="GBE Genesis — Local Diagnostics", lifespan=lifespan)

    @app.get("/health/live")
    def live():
        return {"status": "alive"}

    @app.get("/health/ready")
    def ready():
        try:
            with connect() as db:
                db.execute("SELECT id FROM requests LIMIT 1").fetchone()
        except sqlite3.Error:
            raise HTTPException(503, "Local storage unavailable; check server logs.") from None
        return {"status": "ready", "mode": "local diagnostics", "ai_enabled": False}

    @app.post("/api/requests")
    def submit(request: Request):
        # This milestone authorizes only a local diagnostic, never arbitrary execution.
        request_id = str(uuid4())
        result = "Local request processing and persistence completed. AI reasoning, research and email are not configured."
        try:
            with connect() as db:
                db.execute("INSERT INTO requests VALUES (?, ?, ?, ?)", (request_id, request.action, request.text, result))
        except sqlite3.Error:
            log.exception("Request persistence failed: %s", request_id)
            raise HTTPException(503, "Could not save the request. Check local storage and retry.") from None
        return {"id": request_id, "status": "completed", "result": result}

    @app.post("/api/agent/draft")
    async def agent(request: Request):
        if agent_lock.locked():
            raise HTTPException(429, "An agent draft is already running. Wait for it to finish.")
        async with agent_lock:
            result = await draft(request.text, transport=model_transport)
            request_id = str(uuid4())
            try:
                with connect() as db:
                    db.execute("INSERT INTO requests VALUES (?, ?, ?, ?)", (request_id, "offline_draft", request.text, result))
            except sqlite3.Error:
                log.exception("Draft persistence failed: %s", request_id)
                raise HTTPException(503, "Draft could not be saved. Check local storage.") from None
            return {"id": request_id, "status": "needs_review", "result": result}

    @app.get("/")
    def index():
        return HTMLResponse(PAGE)

    return app


PAGE = """<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>GBE Genesis</title>
<style>body{font:18px system-ui;max-width:720px;margin:60px auto;padding:24px;background:#101a28;color:#eef5ff}textarea{box-sizing:border-box;width:100%;min-height:120px;padding:12px}button{padding:12px 20px;margin-top:16px}pre{white-space:pre-wrap;overflow-wrap:anywhere}small{color:#c0cede}</style>
<h1>GBE Genesis</h1><p>Local startup and request diagnostics</p>
<p id="health" role="status">Checking readiness…</p>
<small>This verifies local request processing and storage. Offline drafting is available when a local model is configured. Drafts require your review; research, email and self-improvement are not enabled. Submitted text is stored on this computer.</small>
<form id="form"><p><label for="text">Describe what you want to check</label></p>
<textarea id="text" maxlength="4000" required></textarea><p><label for="mode">Task</label> <select id="mode"><option value="diagnose">Local diagnostic</option><option value="draft">Offline agent draft</option></select></p><button id="run">Run selected task</button></form>
<pre id="result" role="status" aria-live="polite"></pre>
<script>
async function call(path, options={}, timeout=10000) {
 const controller=new AbortController();
 const timer=setTimeout(()=>controller.abort(),timeout);
 try {
  const response=await fetch(path,{...options,signal:controller.signal});
  const data=await response.json();
  if(!response.ok) throw new Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail));
  return data;
 } catch(error) {
  if(error.name==='AbortError') throw new Error('The request timed out. Check the server window before retrying.');
  throw error;
 } finally {clearTimeout(timer);}
}
call('/health/ready').then(d=>{document.getElementById('health').textContent='Ready — '+d.mode;})
.catch(e=>{document.getElementById('health').textContent='Unavailable: '+e.message;});
document.getElementById('form').addEventListener('submit',async e=>{
 e.preventDefault();
 const button=document.getElementById('run'), output=document.getElementById('result');
 const isDraft=document.getElementById('mode').value==='draft';
 button.disabled=true; output.textContent=isDraft?'Drafting locally — allow up to 90 seconds…':'Running local diagnostic…';
 try {
  const data=await call(isDraft?'/api/agent/draft':'/api/requests',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'diagnose',text:document.getElementById('text').value})},isDraft?100000:10000);
  output.textContent=(isDraft?'DRAFT — REVIEW REQUIRED\\n\\n':'')+data.result+'\\nRequest ID: '+data.id;
 } catch(error) {output.textContent='Failed: '+error.message;}
 finally {button.disabled=false;}
});
</script></html>"""
app = create_app()

