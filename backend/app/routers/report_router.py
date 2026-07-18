from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pypdf import PdfReader
import io

from app.database import get_db
from app.models import Report, User
from app.schemas import ReportOut, ReportDetailOut
from app.auth import get_current_user
from app.agents.report_agent import run_report_agent

router = APIRouter(prefix="/api/reports", tags=["reports"])

MAX_FILE_SIZE_MB = 15


@router.post("/upload", response_model=ReportDetailOut)
async def upload_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit")

    try:
        reader = PdfReader(io.BytesIO(raw))
        text_parts = [page.extract_text() or "" for page in reader.pages]
        extracted_text = "\n".join(text_parts).strip()
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read this PDF. It may be corrupted or scanned/image-only.")

    if not extracted_text:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found. If this is a scanned/image PDF, OCR isn't supported in this MVP.",
        )

    summary = run_report_agent(extracted_text)

    report = Report(
        user_id=current_user.id,
        filename=file.filename,
        extracted_text=extracted_text,
        summary=summary,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return report


@router.get("/", response_model=list[ReportOut])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .order_by(desc(Report.created_at))
        .all()
    )


@router.get("/{report_id}", response_model=ReportDetailOut)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
