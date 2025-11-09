from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import os
import shutil
from ..services.parsing import ingest_files
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
        sales_count, bank_count = ingest_files(excel_path, pdf_path, month)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return UploadResponse(sales_rows=sales_count, bank_rows=bank_count, month=month)
