from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.sql import case
from ..models.models import NormalizedSales, BankTx

REPORT_TEMPLATE = (
    "Monthly Report for {month}: Total gross sales {gross:.2f} with VAT {vat:.2f}. Card share reached {card_share:.2f}%. "
    "Peak sales day was {peak_day} at {peak_gross:.2f}. Top product: {top_product}. "
    "Reconciliation delta aggregate {delta_sum:.2f}. Fees totaled {fees_total:.2f}. "
    "There were {invoice_count} invoices processed. Net amount {net:.2f}. "
    "VAT breakdown: {vat_breakdown}. "
    "Recommendation: optimize fees, monitor anomalies. "
    "Data grounded strictly in ingested records."
)


def monthly_report(db: Session, month: str, recon_rows: list[dict]):
    summary = db.query(
        func.sum(NormalizedSales.gross_amount).label('gross'),
        func.sum(NormalizedSales.vat_amount).label('vat'),
        func.sum(NormalizedSales.net_amount).label('net'),
        func.count(func.distinct(NormalizedSales.invoice_number)
                   ).label('invoice_count'),
        func.sum(case((NormalizedSales.payment_method == 'Cartão Multicaixa',
                       NormalizedSales.gross_amount), else_=0)).label('card')
    ).filter(func.to_char(NormalizedSales.date, 'MM') == month).first()
    vat_rows = db.query(NormalizedSales.vat_rate, func.sum(NormalizedSales.vat_amount)).filter(
        func.to_char(NormalizedSales.date, 'MM') == month).group_by(NormalizedSales.vat_rate).all()
    top_prod = db.query(NormalizedSales.product, func.sum(NormalizedSales.gross_amount).label('g')).filter(func.to_char(
        NormalizedSales.date, 'MM') == month).group_by(NormalizedSales.product).order_by(func.sum(NormalizedSales.gross_amount).desc()).first()
    daily = db.query(NormalizedSales.date, func.sum(NormalizedSales.gross_amount).label('g')).filter(func.to_char(
        NormalizedSales.date, 'MM') == month).group_by(NormalizedSales.date).order_by(func.sum(NormalizedSales.gross_amount).desc()).first()
    fees_total = sum(r['fees'] for r in recon_rows)
    delta_sum = sum(r['delta'] for r in recon_rows)
    vat_breakdown = ', '.join(
        [f"{int(v[0])}%: {float(v[1]):.2f}" for v in vat_rows])
    return REPORT_TEMPLATE.format(
        month=month,
        gross=float(summary.gross or 0),
        vat=float(summary.vat or 0),
        net=float(summary.net or 0),
        card_share=((float(summary.card or 0) /
                    (float(summary.gross or 1))*100)),
        peak_day=daily.date.isoformat() if daily else 'N/A',
        peak_gross=float(daily.g or 0) if daily else 0.0,
        top_product=top_prod.product if top_prod else 'N/A',
        delta_sum=delta_sum,
        fees_total=fees_total,
        invoice_count=summary.invoice_count or 0,
        vat_breakdown=vat_breakdown
    )

# Chat answer stub grounded: simply returns monthly report or clarifies delta explanation request


def answer(db: Session, month: str, question: str, recon_rows: list[dict]):
    qlower = question.lower()
    if 'report' in qlower or 'monthly' in qlower:
        return monthly_report(db, month, recon_rows)
    if 'why' in qlower and 'delta' in qlower:
        largest = sorted(recon_rows, key=lambda r: abs(
            r['delta']), reverse=True)[:3]
        parts = []
        for r in largest:
            parts.append(
                f"Date {r['date']} delta {r['delta']:.2f} due to fees {r['fees']:.2f} vs bank {r['bank_tpa']:.2f}")
        return "Mismatches: " + '; '.join(parts)
    # fallback simple factual summary
    summary = monthly_report(db, month, recon_rows)
    return "Contextual Answer: " + summary
