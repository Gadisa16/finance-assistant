from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.metrics import anomalies

router = APIRouter(prefix="/quality", tags=["quality"])


@router.get('/anomalies')
async def get_anomalies(month: str, db: Session = Depends(get_db)):
    return anomalies(db, month)
