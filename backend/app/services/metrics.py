from datetime import date
from typing import List, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.sql import case

from ..models.models import NormalizedSales, BankTx, ReconciliationCache

ALLOWED_VAT = [0, 5, 7, 14]


def _month_filter(month: str):
    """Return a SQLAlchemy expression filtering NormalizedSales.date by month string 'MM'."""
    return func.to_char(NormalizedSales.date, 'MM') == month


def kpi_summary(db: Session, month: str) -> Optional[Dict]:
    """Return total net, vat, gross and card/cash split for the month."""
    card_case = case((NormalizedSales.payment_method ==
                     'Cartão Multicaixa', NormalizedSales.gross_amount), else_=0)
    cash_case = case((NormalizedSales.payment_method ==
                     'Numerário', NormalizedSales.gross_amount), else_=0)

    q = (
        db.query(
            func.coalesce(func.sum(NormalizedSales.net_amount),
                          0).label('net'),
            func.coalesce(func.sum(NormalizedSales.vat_amount),
                          0).label('vat'),
            func.coalesce(func.sum(NormalizedSales.gross_amount),
                          0).label('gross'),
            func.coalesce(func.sum(card_case), 0).label('card'),
            func.coalesce(func.sum(cash_case), 0).label('cash'),
        )
        .filter(_month_filter(month))
    )

    res = q.first()
    if not res or res.gross is None:
        return None

    gross = float(res.gross)
    card = float(res.card)

    return {
        'month': month,
        'total_net': float(res.net),
        'total_vat': float(res.vat),
        'total_gross': gross,
        'card_gross': card,
        'cash_gross': float(res.cash),
        'card_share_pct': round((card / (gross or 1)) * 100, 2),
    }


def kpi_daily(db: Session, month: str) -> List[Dict]:
    card_case = case((NormalizedSales.payment_method ==
                     'Cartão Multicaixa', NormalizedSales.gross_amount), else_=0)
    cash_case = case((NormalizedSales.payment_method ==
                     'Numerário', NormalizedSales.gross_amount), else_=0)

    rows = (
        db.query(
            NormalizedSales.date,
            func.coalesce(func.sum(NormalizedSales.gross_amount),
                          0).label('gross'),
            func.coalesce(func.sum(card_case), 0).label('card'),
            func.coalesce(func.sum(cash_case), 0).label('cash'),
        )
        .filter(_month_filter(month))
        .group_by(NormalizedSales.date)
        .order_by(NormalizedSales.date)
        .all()
    )

    return [
        {
            'date': r.date.isoformat(),
            'gross': float(r.gross),
            'card': float(r.card),
            'cash': float(r.cash),
        }
        for r in rows
    ]


def kpi_top_products(db: Session, month: str, limit: int = 10) -> List[Dict]:
    rows = (
        db.query(NormalizedSales.product, func.coalesce(
            func.sum(NormalizedSales.gross_amount), 0).label('gross'))
        .filter(_month_filter(month))
        .group_by(NormalizedSales.product)
        .order_by(func.sum(NormalizedSales.gross_amount).desc())
        .limit(limit)
        .all()
    )
    return [{'product': r.product, 'gross': float(r.gross)} for r in rows]


def kpi_top_customers(db: Session, month: str, limit: int = 10) -> List[Dict]:
    rows = (
        db.query(NormalizedSales.customer, func.coalesce(
            func.sum(NormalizedSales.gross_amount), 0).label('gross'))
        .filter(_month_filter(month))
        .group_by(NormalizedSales.customer)
        .order_by(func.sum(NormalizedSales.gross_amount).desc())
        .limit(limit)
        .all()
    )
    return [{'customer': r.customer, 'gross': float(r.gross)} for r in rows]


def vat_report(db: Session, month: str) -> List[Dict]:
    rows = (
        db.query(
            NormalizedSales.vat_rate,
            func.coalesce(func.sum(NormalizedSales.net_amount),
                          0).label('net'),
            func.coalesce(func.sum(NormalizedSales.vat_amount),
                          0).label('vat'),
            func.coalesce(func.sum(NormalizedSales.gross_amount),
                          0).label('gross'),
        )
        .filter(_month_filter(month))
        .group_by(NormalizedSales.vat_rate)
        .order_by(NormalizedSales.vat_rate)
        .all()
    )

    return [
        {
            'vat_rate': float(r.vat_rate),
            'net': float(r.net),
            'vat': float(r.vat),
            'gross': float(r.gross),
        }
        for r in rows
    ]


def anomalies(db: Session, month: str) -> Dict:
    # Duplicate invoice numbers (more than 1), negative amounts
    dup_invoices = (
        db.query(NormalizedSales.invoice_number,
                 func.count(NormalizedSales.id).label('cnt'))
        .filter(_month_filter(month))
        .group_by(NormalizedSales.invoice_number)
        .having(func.count(NormalizedSales.id) > 1)
        .all()
    )

    negatives = (
        db.query(NormalizedSales)
        .filter(_month_filter(month), NormalizedSales.gross_amount < 0)
        .limit(50)
        .all()
    )

    return {
        'duplicate_invoices': [{'invoice_number': d.invoice_number, 'lines': d.cnt} for d in dup_invoices],
        'negative_lines': [{'invoice_number': n.invoice_number, 'gross': float(n.gross_amount)} for n in negatives],
    }


"""Financial metrics and reconciliation services.

This module provides KPI aggregations and a simple reconciliation between
card sales and bank FECHO_TPA credits. Uses SQLAlchemy 2.x compatible case().
"""


def _month_filter(month: str):
    """Filter expression for a month string 'MM'."""
    return func.to_char(NormalizedSales.date, 'MM') == month


def _payment_case(method: str):
    """Helper returning a CASE selecting gross_amount when payment method matches."""
    return case((NormalizedSales.payment_method == method, NormalizedSales.gross_amount), else_=0)


def kpi_summary(db: Session, month: str) -> Optional[Dict]:
    card_case = _payment_case('Cartão Multicaixa')
    cash_case = _payment_case('Numerário')

    res = (
        db.query(
            func.coalesce(func.sum(NormalizedSales.net_amount),
                          0).label('net'),
            func.coalesce(func.sum(NormalizedSales.vat_amount),
                          0).label('vat'),
            func.coalesce(func.sum(NormalizedSales.gross_amount),
                          0).label('gross'),
            func.coalesce(func.sum(card_case), 0).label('card'),
            func.coalesce(func.sum(cash_case), 0).label('cash'),
        )
        .filter(_month_filter(month))
        .first()
    )
    if not res or res.gross is None:
        return None
    gross = float(res.gross)
    card = float(res.card)
    return {
        'month': month,
        'total_net': float(res.net),
        'total_vat': float(res.vat),
        'total_gross': gross,
        'card_gross': card,
        'cash_gross': float(res.cash),
        'card_share_pct': round((card / (gross or 1)) * 100, 2),
    }


def kpi_daily(db: Session, month: str) -> List[Dict]:
    card_case = _payment_case('Cartão Multicaixa')
    cash_case = _payment_case('Numerário')
    rows = (
        db.query(
            NormalizedSales.date,
            func.coalesce(func.sum(NormalizedSales.gross_amount),
                          0).label('gross'),
            func.coalesce(func.sum(card_case), 0).label('card'),
            func.coalesce(func.sum(cash_case), 0).label('cash'),
        )
        .filter(_month_filter(month))
        .group_by(NormalizedSales.date)
        .order_by(NormalizedSales.date)
        .all()
    )
    return [
        {
            'date': r.date.isoformat(),
            'gross': float(r.gross),
            'card': float(r.card),
            'cash': float(r.cash),
        }
        for r in rows
    ]


def kpi_top_products(db: Session, month: str, limit: int = 10) -> List[Dict]:
    rows = (
        db.query(
            NormalizedSales.product,
            func.coalesce(func.sum(NormalizedSales.gross_amount),
                          0).label('gross'),
        )
        .filter(_month_filter(month))
        .group_by(NormalizedSales.product)
        .order_by(func.sum(NormalizedSales.gross_amount).desc())
        .limit(limit)
        .all()
    )
    return [{'product': r.product, 'gross': float(r.gross)} for r in rows]


def kpi_top_customers(db: Session, month: str, limit: int = 10) -> List[Dict]:
    rows = (
        db.query(
            NormalizedSales.customer,
            func.coalesce(func.sum(NormalizedSales.gross_amount),
                          0).label('gross'),
        )
        .filter(_month_filter(month))
        .group_by(NormalizedSales.customer)
        .order_by(func.sum(NormalizedSales.gross_amount).desc())
        .limit(limit)
        .all()
    )
    return [{'customer': r.customer, 'gross': float(r.gross)} for r in rows]


def vat_report(db: Session, month: str) -> List[Dict]:
    rows = (
        db.query(
            NormalizedSales.vat_rate,
            func.coalesce(func.sum(NormalizedSales.net_amount),
                          0).label('net'),
            func.coalesce(func.sum(NormalizedSales.vat_amount),
                          0).label('vat'),
            func.coalesce(func.sum(NormalizedSales.gross_amount),
                          0).label('gross'),
        )
        .filter(_month_filter(month))
        .group_by(NormalizedSales.vat_rate)
        .order_by(NormalizedSales.vat_rate)
        .all()
    )
    return [
        {
            'vat_rate': float(r.vat_rate),
            'net': float(r.net),
            'vat': float(r.vat),
            'gross': float(r.gross),
        }
        for r in rows
    ]


def anomalies(db: Session, month: str) -> Dict:
    dup_invoices = (
        db.query(NormalizedSales.invoice_number,
                 func.count(NormalizedSales.id).label('cnt'))
        .filter(_month_filter(month))
        .group_by(NormalizedSales.invoice_number)
        .having(func.count(NormalizedSales.id) > 1)
        .all()
    )
    negatives = (
        db.query(NormalizedSales)
        .filter(_month_filter(month), NormalizedSales.gross_amount < 0)
        .limit(50)
        .all()
    )
    return {
        'duplicate_invoices': [{'invoice_number': d.invoice_number, 'lines': d.cnt} for d in dup_invoices],
        'negative_lines': [{'invoice_number': n.invoice_number, 'gross': float(n.gross_amount)} for n in negatives],
    }


def reconciliation(db: Session, month: str) -> List[Dict]:
    """Reconcile daily card sales vs FECHO_TPA credits.

    ReconciliationCache schema: (date, sales_card, bank_tpa, fees, delta, detail_json)
    We store fees as 0 for now (future: derive commissions), delta = sales_card - bank_tpa - fees.
    detail_json contains a compact JSON summary.
    """
    # Daily card sales
    sales_rows = (
        db.query(NormalizedSales.date, func.coalesce(
            func.sum(NormalizedSales.gross_amount), 0).label('card_gross'))
        .filter(_month_filter(month), NormalizedSales.payment_method == 'Cartão Multicaixa')
        .group_by(NormalizedSales.date)
        .all()
    )
    # Bank credits
    bank_rows = (
        db.query(BankTx.date, func.coalesce(
            func.sum(BankTx.credit), 0).label('bank_credit'))
        .filter(BankTx.tx_type == 'FECHO_TPA', func.to_char(BankTx.date, 'MM') == month)
        .group_by(BankTx.date)
        .all()
    )
    bank_map = {b.date: float(b.bank_credit) for b in bank_rows}

    results: List[Dict] = []
    db.query(ReconciliationCache).filter(ReconciliationCache.date.in_(
        [r.date for r in sales_rows])).delete(synchronize_session=False)
    for s in sales_rows:
        card = float(s.card_gross)
        bank = bank_map.get(s.date, 0.0)
        fees = 0.0  # placeholder
        delta = round(card - bank - fees, 2)
        detail_json = f"{{\"card\":{card},\"bank\":{bank},\"fees\":{fees}}}"
        cache = ReconciliationCache(
            date=s.date, sales_card=card, bank_tpa=bank, fees=fees, delta=delta, detail_json=detail_json)
        db.add(cache)
        results.append({
            'date': s.date.isoformat(),
            'sales_card': card,
            'bank_tpa': bank,
            'fees': fees,
            'delta': delta,
        })
    try:
        db.commit()
    except Exception:
        db.rollback()
    return results
