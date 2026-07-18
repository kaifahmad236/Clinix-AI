from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import ChatMessage, User
from app.schemas import SessionSummary
from app.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/sessions", response_model=list[SessionSummary])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    sessions: dict[str, dict] = {}
    for m in rows:
        s = sessions.setdefault(
            m.session_id,
            {"session_id": m.session_id, "message_count": 0},
        )
        s["message_count"] += 1
        s["last_message"] = m.content
        s["last_role"] = m.role
        s["updated_at"] = m.created_at

    summaries = sorted(sessions.values(), key=lambda s: s["updated_at"], reverse=True)
    return summaries
