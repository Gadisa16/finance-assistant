from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.metrics import reconciliation
from ..llm.stub import answer

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    month: str
    question: str


class ChatResponse(BaseModel):
    answer: str


@router.post('/ask', response_model=ChatResponse)
async def ask(req: ChatRequest, db: Session = Depends(get_db)):
    recon_rows = reconciliation(db, req.month)
    ans = answer(db, req.month, req.question, recon_rows)
    return ChatResponse(answer=ans)
