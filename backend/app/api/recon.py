from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.metrics import reconciliation

router = APIRouter(prefix="/recon", tags=["recon"])


@router.get('/card')
async def recon_card(month: str, db: Session = Depends(get_db)):
    return reconciliation(db, month)
