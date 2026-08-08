"""
Copilot Backend API
Exposes the orchestrator as HTTP endpoints consumed by the Gradio frontend.
"""
import logging
import uuid
import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

from orch import CopilotOrchestrator

app = FastAPI(title="Incident Copilot API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

orchestrator = CopilotOrchestrator()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class ConfirmRequest(BaseModel):
    draft_id: str
    confirmed_by: str = "operator"


@app.get("/health")
def health():
    return {"status": "ok", "service": "copilot-backend"}


@app.post("/chat")
async def chat(req: ChatRequest):
    """Main chat endpoint — runs the full orchestration pipeline."""
    conversation_id = req.conversation_id or str(uuid.uuid4())
    try:
        result = await orchestrator.handle(
            user_message=req.message,
            conversation_id=conversation_id,
        )
        return result
    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/confirm-ticket")
async def confirm_ticket(req: ConfirmRequest):
    """Confirms ticket creation after user approval — WRITE operation."""
    try:
        ticket = await orchestrator.confirm_ticket(
            draft_id=req.draft_id,
            confirmed_by=req.confirmed_by,
        )
        return {"status": "created", "ticket": ticket}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Confirm ticket error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/drafts/{draft_id}")
async def get_draft(draft_id: str):
    draft = await orchestrator.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@app.get("/tickets")
async def list_tickets():
    tickets = await orchestrator.list_tickets()
    return {"tickets": tickets}