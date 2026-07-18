import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from app.database import get_db
from app.models import ChatMessage, Report, User
from app.schemas import ChatRequest, ChatResponse, ChatMessageOut
from app.auth import get_current_user
from app.agents.orchestrator import run_orchestrator

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/send", response_model=ChatResponse)
def send_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_id = payload.session_id or str(uuid.uuid4())

    # Pull prior turns in this session for conversational memory.
    prior = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id, ChatMessage.session_id == session_id)
        .order_by(asc(ChatMessage.created_at))
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in prior]

    # Latest report summary (if any) gives the orchestrator context to work with.
    latest_report = (
        db.query(Report)
        .filter(Report.user_id == current_user.id, Report.summary.isnot(None))
        .order_by(desc(Report.created_at))
        .first()
    )
    latest_summary = latest_report.summary if latest_report else None

    result = run_orchestrator(
        message=payload.message,
        history=history,
        latest_report_summary=latest_summary,
    )

    # Persist both turns.
    user_msg = ChatMessage(
        session_id=session_id,
        user_id=current_user.id,
        role="user",
        content=payload.message,
        agent_used="user",
    )
    ai_msg = ChatMessage(
        session_id=session_id,
        user_id=current_user.id,
        role="assistant",
        content=result["reply"],
        agent_used=result["agent_used"],
    )
    db.add_all([user_msg, ai_msg])
    db.commit()

    return ChatResponse(session_id=session_id, reply=result["reply"], agent_used=result["agent_used"])


@router.get("/history/{session_id}", response_model=list[ChatMessageOut])
def get_session_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    msgs = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id, ChatMessage.session_id == session_id)
        .order_by(asc(ChatMessage.created_at))
        .all()
    )
    return msgs
