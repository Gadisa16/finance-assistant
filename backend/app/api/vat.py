from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.metrics import vat_report
import csv
from io import StringIO
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/vat", tags=["vat"])


@router.get('/report')
async def report(month: str, db: Session = Depends(get_db)):
    return vat_report(db, month)


@router.get('/export')
async def export_csv(month: str, db: Session = Depends(get_db)):
    data = vat_report(db, month)
    si = StringIO()
    writer = csv.DictWriter(si, fieldnames=['vat_rate', 'net', 'vat', 'gross'])
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    si.seek(0)
    return StreamingResponse(iter([si.getvalue()]), media_type='text/csv', headers={'Content-Disposition': f'attachment; filename="vat_{month}.csv"'})
