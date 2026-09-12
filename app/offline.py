"""Supervised local drafting only; no tools, cloud fallback or shell execution."""
import asyncio
import os

import httpx
from fastapi import HTTPException


async def draft(text, transport=None):
    model = os.environ.get("GBE_LOCAL_MODEL", "").strip()
    if not model:
        raise HTTPException(503, "Set GBE_LOCAL_MODEL to an installed Ollama model, then restart GBE.")
    if "cloud" in model.lower():
        raise HTTPException(400, "Cloud models are disabled. Choose an installed local model.")
    try:
        # Fixed loopback endpoint and no proxy/redirect support prevent remote routing.
        async with asyncio.timeout(90):
            async with httpx.AsyncClient(base_url="http://127.0.0.1:11434", trust_env=False,
                                         follow_redirects=False, timeout=85, transport=transport) as client:
                response = await client.post("/api/chat", json={
                    "model": model, "stream": False,
                    "messages": [
                        {"role": "system", "content": "You are GBE's supervised drafting assistant. Produce a practical draft or plan from the user's text. State uncertainties. You have no tools and cannot execute actions, send email, browse, or modify files. Never claim you performed those actions."},
                        {"role": "user", "content": text},
                    ],
                    "options": {"num_predict": 1024},
                })
                if response.status_code == 404:
                    raise HTTPException(503, "Model not found. Install the selected model in Ollama first.")
                response.raise_for_status()
                data = response.json()
                message = data.get("message", {})
                result = message.get("content")
                if data.get("done") is not True or message.get("tool_calls") or not isinstance(result, str) or not result.strip():
                    raise ValueError("Incomplete or unsupported model response")
                return result.strip()
    except (TimeoutError, httpx.TimeoutException):
        raise HTTPException(504, "Local model timed out after at most 90 seconds. Try a smaller model or shorter request.") from None
    except httpx.ConnectError:
        raise HTTPException(503, "Ollama is unavailable. Start Ollama on this computer and retry.") from None
    except (httpx.HTTPError, ValueError, AttributeError, TypeError):
        raise HTTPException(502, "Local model returned an invalid response. Check Ollama's status and model configuration.") from None
