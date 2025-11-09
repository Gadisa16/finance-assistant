from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Numeric, Text, Enum, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import enum


class PaymentMethod(str, enum.Enum):
    CARTAO = "Cartão Multicaixa"
    NUMERARIO = "Numerário"


class RawSales(Base):
    __tablename__ = 'raw_sales'
    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)  # excel filename
    raw_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class NormalizedSales(Base):
    __tablename__ = 'normalized_sales'
    id = Column(Integer, primary_key=True)
    date = Column(Date, index=True, nullable=False)
    invoice_number = Column(String(100), index=True, nullable=False)
    customer = Column(String(255), default="Consumidor Final")
    product = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price_net = Column(Numeric(18, 2), nullable=False)
    vat_rate = Column(Float, nullable=False)  # 0,5,7,14
    net_amount = Column(Numeric(18, 2), nullable=False)
    vat_amount = Column(Numeric(18, 2), nullable=False)
    gross_amount = Column(Numeric(18, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


Index('idx_sales_month', NormalizedSales.date)


class BankTx(Base):
    __tablename__ = 'bank_tx'
    id = Column(Integer, primary_key=True)
    date = Column(Date, index=True, nullable=False)
    description = Column(Text, nullable=False)
    debit = Column(Numeric(18, 2))
    credit = Column(Numeric(18, 2))
    balance = Column(Numeric(18, 2))
    # FECHO_TPA, COMISSAO_STC, IVA_COMISSAO, TRANSF_INTERNA, RESERVA, OTHER
    tx_type = Column(String(50), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReconciliationCache(Base):
    __tablename__ = 'reconciliation_cache'
    id = Column(Integer, primary_key=True)
    date = Column(Date, index=True, nullable=False)
    sales_card = Column(Numeric(18, 2), nullable=False)
    bank_tpa = Column(Numeric(18, 2), nullable=False)
    fees = Column(Numeric(18, 2), nullable=False)
    delta = Column(Numeric(18, 2), nullable=False)
    detail_json = Column(Text, nullable=False)  # stores which lines were used
    created_at = Column(DateTime(timezone=True), server_default=func.now())
