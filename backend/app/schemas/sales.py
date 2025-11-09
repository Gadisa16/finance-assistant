from pydantic import BaseModel
from datetime import date
from typing import Optional


class NormalizedSaleBase(BaseModel):
    date: date
    invoice_number: str
    customer: str
    product: str
    quantity: float
    unit_price_net: float
    vat_rate: float
    net_amount: float
    vat_amount: float
    gross_amount: float
    payment_method: str


class NormalizedSale(NormalizedSaleBase):
    id: int

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    sales_rows: int
    bank_rows: int
    month: str
