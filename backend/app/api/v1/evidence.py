import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.enums import RoleEnum, EvidenceTypeEnum
from app.models.problem import Problem
from app.models.evidence import Evidence
from app.models.user import User
from app.schemas.extra import EvidenceOut
from app.services.voice_to_text import transcribe_audio
from app.services.storage_service import save_file
from app.services.pipeline import run_analysis

router = APIRouter(prefix="/problems/{problem_id}/evidence", tags=["evidence"])


@router.post("", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
def upload_evidence(
    problem_id: str,
    file: UploadFile = File(...),
    type: EvidenceTypeEnum = EvidenceTypeEnum.DOCUMENT,
    transcript: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload an evidence file (image/video/audio/document). Audio is auto-transcribed.

    A client-supplied `transcript` (e.g. from Puter.js in the browser) is preferred;
    otherwise server-side STT (Cloudflare Whisper) is used as fallback.
    """
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    content = file.file.read()
    file_url = save_file(content, file.filename or "upload.bin")

    transcript_text = None
    if type == EvidenceTypeEnum.AUDIO:
        if transcript and transcript.strip():
            transcript_text = transcript.strip()
        else:
            transcript_text = transcribe_audio(content, file.filename or "audio")

    evidence = Evidence(
        problem_id=problem_id,
        type=type,
        file_url=file_url,
        transcript=transcript_text,
        uploaded_by_id=current_user.id,
    )
    db.add(evidence)

    # Feed transcript into the problem so the AI pipeline can use spoken content.
    if transcript_text:
        existing = problem.evidence_text or ""
        problem.evidence_text = (existing + "\n" + transcript_text).strip() if existing else transcript_text

    db.commit()
    db.refresh(evidence)

    # Re-run analysis so the new evidence improves categorization / priority.
    if transcript_text:
        try:
            run_analysis(db, problem)
        except Exception:
            db.rollback()

    return evidence


@router.get("", response_model=list[EvidenceOut])
def list_evidence(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return db.query(Evidence).filter(Evidence.problem_id == problem_id).order_by(Evidence.created_at.desc()).all()
