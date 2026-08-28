from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.enums import RoleEnum
from app.models.problem import Problem
from app.models.user import User
from app.schemas.extra import AnalysisOut
from app.services.pipeline import run_analysis
from app.services import ai_categorization

router = APIRouter(prefix="/ai", tags=["ai"])


class TagExtractRequest(BaseModel):
    title: str
    description: str
    transcript: str = ""


@router.post("/extract-tags")
def extract_tags(
    body: TagExtractRequest,
    current_user: User = Depends(get_current_user),
):
    """Use the LLM/heuristic to extract relevant tags from a problem title + description.
    Returns a list of {id, name, confidence} tag objects — no DB writes.
    """
    result = ai_categorization.categorize(
        body.title.strip(),
        body.description.strip(),
        body.transcript.strip() or None,
        tags=None,
    )
    return {
        "category": result["category_name"],
        "priority": result["priority"].value,
        "tags": result["tags"],  # [{id, name, confidence}]
    }


class TranslateRequest(BaseModel):
    text: str
    target_language: str


@router.post("/translate")
def translate_text(
    body: TranslateRequest,
    current_user: User = Depends(get_current_user),
):
    """Use the LLM to translate text to a target language. Used for voice notes and problem viewing."""
    from app.services.cloudflare_ai import chat
    
    prompt = (
        f"You are a professional translator. Translate the following text into {body.target_language}. "
        "Maintain the original meaning, tone, and any technical terms if they don't have a direct translation. "
        "Respond ONLY with the translated text, with no introductory or conversational prose."
    )
    
    result = chat([
        {"role": "system", "content": prompt},
        {"role": "user", "content": body.text}
    ], model="@cf/meta/llama-3.1-8b-instruct")
    
    if not result:
        raise HTTPException(status_code=503, detail="Translation service is temporarily unavailable.")
        
    return {"translated_text": result.strip()}


@router.post("/analyze/{problem_id}", response_model=AnalysisOut)
def analyze(
    problem_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run the full AI pipeline (categorize + prioritize + dedupe + route) on a problem."""
    problem = db.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    if problem.submitter_id != current_user.id and current_user.role not in [
        RoleEnum.ADMIN, RoleEnum.GOVERNMENT, RoleEnum.UNIVERSITY_ADMIN, RoleEnum.FACULTY
    ]:
        raise HTTPException(status_code=403, detail="Not authorized to analyze this problem")
    return run_analysis(db, problem)
