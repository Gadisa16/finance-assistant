from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.metrics import reconciliation
from ..llm.stub import answer
from ..config import settings
from ..llm.groq import answer_groq

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    month: str
    question: str


class ChatResponse(BaseModel):
    answer: str


@router.post('/ask', response_model=ChatResponse)
async def ask(req: ChatRequest, db: Session = Depends(get_db)):
    recon_rows = reconciliation(db, req.month)
    # If LLM_API_URL points to an HTTP endpoint, use OpenAI-compatible path (e.g., Groq)
    if settings.llm_api_url and settings.llm_api_url.startswith('http'):
        ans = await answer_groq(db, req.month, req.question, recon_rows)
        return ChatResponse(answer=ans)
    # Otherwise, use local stub
    try:
        ans = answer(db, req.month, req.question, recon_rows)
    except Exception as e:
        ans = f"Unable to generate chat answer: {e}. Please ensure data is uploaded for the month."
    return ChatResponse(answer=ans)
