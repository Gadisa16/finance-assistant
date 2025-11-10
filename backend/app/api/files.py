from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import os
import shutil
from ..services.parsing import ingest_files, detect_excel_months, detect_bank_months
from ..schemas.sales import UploadResponse
from ..config import settings

router = APIRouter(prefix="/files", tags=["files"])


@router.post('/upload', response_model=UploadResponse)
async def upload_files(month: str, sales_excel: UploadFile = File(...), bank_pdf: UploadFile = File(...)):
    os.makedirs(settings.upload_dir, exist_ok=True)
    excel_path = os.path.join(settings.upload_dir, sales_excel.filename)
    pdf_path = os.path.join(settings.upload_dir, bank_pdf.filename)
    with open(excel_path, 'wb') as f:
        shutil.copyfileobj(sales_excel.file, f)
    with open(pdf_path, 'wb') as f:
        shutil.copyfileobj(bank_pdf.file, f)
    try:
        # Validate that requested month exists in at least one of the files to avoid silent zeros
        excel_months = detect_excel_months(excel_path)
        bank_months = detect_bank_months(pdf_path)
        if month not in excel_months and month not in bank_months:
            detail = {
                'error': 'month_mismatch',
                'requested_month': month,
                'excel_months_found': sorted(list(excel_months)),
                'bank_months_found': sorted(list(bank_months)),
                'hint': 'Upload files that contain the requested month or set month to one present in the files.'
            }
            raise HTTPException(status_code=400, detail=detail)
        sales_count, bank_count = ingest_files(excel_path, pdf_path, month)
    except Exception as e:
        # FastAPI will not double-wrap HTTPException
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail=str(e))
    return UploadResponse(sales_rows=sales_count, bank_rows=bank_count, month=month)
