from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date
from typing import List, Dict
from ..models.models import NormalizedSales, BankTx, ReconciliationCache
import json

ALLOWED_VAT = [0, 5, 7, 14]


def _month_filter(month: str):
    # month string '09'; filter by month on date
    return func.to_char(NormalizedSales.date, 'MM') == month


def kpi_summary(db: Session, month: str):
    q = db.query(
        func.sum(NormalizedSales.net_amount).label('net'),
        func.sum(NormalizedSales.vat_amount).label('vat'),
        func.sum(NormalizedSales.gross_amount).label('gross'),
        func.sum(func.case((NormalizedSales.payment_method == 'Cartão Multicaixa',
                 NormalizedSales.gross_amount), else_=0)).label('card'),
        func.sum(func.case((NormalizedSales.payment_method == 'Numerário',
                 NormalizedSales.gross_amount), else_=0)).label('cash')
    ).filter(_month_filter(month))
    res = q.first()
    if not res or res.gross is None:
        return None
    return {
        'month': month,
        'total_net': float(res.net or 0),
        'total_vat': float(res.vat or 0),
        'total_gross': float(res.gross or 0),
        'card_gross': float(res.card or 0),
        'cash_gross': float(res.cash or 0),
        'card_share_pct': round((float(res.card or 0) / float(res.gross or 1))*100, 2)
    }


def kpi_daily(db: Session, month: str):
    rows = db.query(
        NormalizedSales.date,
        func.sum(NormalizedSales.gross_amount).label('gross'),
        func.sum(func.case((NormalizedSales.payment_method == 'Cartão Multicaixa',
                 NormalizedSales.gross_amount), else_=0)).label('card'),
        func.sum(func.case((NormalizedSales.payment_method == 'Numerário',
                 NormalizedSales.gross_amount), else_=0)).label('cash')
    ).filter(_month_filter(month)).group_by(NormalizedSales.date).order_by(NormalizedSales.date).all()
    return [
        {
            'date': r.date.isoformat(),
            'gross': float(r.gross or 0),
            'card': float(r.card or 0),
            'cash': float(r.cash or 0)
        } for r in rows
    ]


def kpi_top_products(db: Session, month: str, limit: int = 10):
    rows = db.query(
        NormalizedSales.product,
        func.sum(NormalizedSales.gross_amount).label('gross')
    ).filter(_month_filter(month)).group_by(NormalizedSales.product).order_by(func.sum(NormalizedSales.gross_amount).desc()).limit(limit).all()
    return [{'product': r.product, 'gross': float(r.gross or 0)} for r in rows]


def kpi_top_customers(db: Session, month: str, limit: int = 10):
    rows = db.query(
        NormalizedSales.customer,
        func.sum(NormalizedSales.gross_amount).label('gross')
    ).filter(_month_filter(month)).group_by(NormalizedSales.customer).order_by(func.sum(NormalizedSales.gross_amount).desc()).limit(limit).all()
    return [{'customer': r.customer, 'gross': float(r.gross or 0)} for r in rows]


def vat_report(db: Session, month: str):
    rows = db.query(
        NormalizedSales.vat_rate,
        func.sum(NormalizedSales.net_amount).label('net'),
        func.sum(NormalizedSales.vat_amount).label('vat'),
        func.sum(NormalizedSales.gross_amount).label('gross')
    ).filter(_month_filter(month)).group_by(NormalizedSales.vat_rate).order_by(NormalizedSales.vat_rate).all()
    return [
        {
            'vat_rate': float(r.vat_rate),
            'net': float(r.net or 0),
            'vat': float(r.vat or 0),
            'gross': float(r.gross or 0)
        } for r in rows
    ]


def anomalies(db: Session, month: str):
    # Duplicate invoice numbers, negative amounts
    dup_invoices = db.query(NormalizedSales.invoice_number, func.count('*').label('cnt')).filter(
        _month_filter(month)).group_by(NormalizedSales.invoice_number).having(func.count('*') > 50).all()
    negatives = db.query(NormalizedSales).filter(_month_filter(
        month), NormalizedSales.gross_amount < 0).limit(20).all()
    return {
        'duplicate_invoices': [{'invoice_number': d.invoice_number, 'lines': d.cnt} for d in dup_invoices],
        'negative_lines': [{'invoice_number': n.invoice_number, 'gross': float(n.gross_amount)} for n in negatives]
    }


def reconciliation(db: Session, month: str):
    # Build daily card sales
    daily_sales = db.query(
        NormalizedSales.date,
        func.sum(NormalizedSales.gross_amount).label('card_gross')
    ).filter(_month_filter(month), NormalizedSales.payment_method == 'Cartão Multicaixa').group_by(NormalizedSales.date).all()
    # Bank FECHO TPA credits and fees per date
    tpa = db.query(BankTx.date, func.sum(BankTx.credit).label('credit')).filter(
        BankTx.tx_type == 'FECHO_TPA', func.to_char(BankTx.date, 'MM') == month).group_by(BankTx.date).all()
    fees = db.query(BankTx.date, func.sum(func.coalesce(BankTx.debit, 0)).label('fees')).filter(BankTx.tx_type.in_(
        ['COMISSAO_STC', 'IVA_COMISSAO']), func.to_char(BankTx.date, 'MM') == month).group_by(BankTx.date).all()
    tpa_map = {r.date: float(r.credit or 0) for r in tpa}
    fees_map = {r.date: float(r.fees or 0) for r in fees}

    results = []
    for ds in daily_sales:
        d = ds.date
        sales_card = float(ds.card_gross or 0)
        # T+1 logic: prefer same day else next day credit
        bank_credit = tpa_map.get(d)
        if bank_credit is None:
            # cannot cast like this in Python; fallback manual next-day search
            bank_credit = tpa_map.get(
                d + func.cast(func.interval('1 day'), type(d)))
        # Manual next day search
        if bank_credit is None:
            next_day = date.fromordinal(d.toordinal()+1)
            bank_credit = tpa_map.get(next_day, 0.0)
        fee_total = fees_map.get(d, 0.0)
        delta = round(sales_card - (bank_credit - fee_total), 2)
        detail = {'date': d.isoformat(), 'sales_card': sales_card,
                  'bank_tpa': bank_credit, 'fees': fee_total, 'delta': delta}
        results.append(detail)
    # store cache (truncate month first?)
    for r in results:
        db.merge(ReconciliationCache(date=date.fromisoformat(
            r['date']), sales_card=r['sales_card'], bank_tpa=r['bank_tpa'], fees=r['fees'], delta=r['delta'], detail_json=json.dumps(r)))
    db.commit()
    return results
