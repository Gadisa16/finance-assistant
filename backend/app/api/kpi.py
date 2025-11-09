from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.metrics import kpi_summary, kpi_daily, kpi_top_customers, kpi_top_products

router = APIRouter(prefix="/kpi", tags=["kpi"])


@router.get('/summary')
async def summary(month: str, db: Session = Depends(get_db)):
    res = kpi_summary(db, month)
    if not res:
        raise HTTPException(status_code=404, detail="No data")
    return res


@router.get('/daily')
async def daily(month: str, db: Session = Depends(get_db)):
    return kpi_daily(db, month)


@router.get('/top-customers')
async def top_customers(month: str, limit: int = 10, db: Session = Depends(get_db)):
    return kpi_top_customers(db, month, limit)


@router.get('/top-products')
async def top_products(month: str, limit: int = 10, db: Session = Depends(get_db)):
    return kpi_top_products(db, month, limit)
