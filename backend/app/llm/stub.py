from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.sql import case
from ..models.models import NormalizedSales

REPORT_TEMPLATE = (
    "Monthly Report for {month}: Total gross sales {gross:.2f} with VAT {vat:.2f}. Card share reached {card_share:.2f}%. "
    "Peak sales day was {peak_day} at {peak_gross:.2f}. Top product: {top_product}. "
    "Reconciliation delta aggregate {delta_sum:.2f}. Fees totaled {fees_total:.2f}. "
    "There were {invoice_count} invoices processed. Net amount {net:.2f}. "
    "VAT breakdown: {vat_breakdown}. "
    "Recommendation: optimize fees, monitor anomalies. "
    "Data grounded strictly in ingested records."
)


def _facts(db: Session, month: str, recon_rows: list[dict]):
    summary = db.query(
        func.coalesce(func.sum(NormalizedSales.gross_amount),
                      0).label('gross'),
        func.coalesce(func.sum(NormalizedSales.vat_amount), 0).label('vat'),
        func.coalesce(func.sum(NormalizedSales.net_amount), 0).label('net'),
        func.count(func.distinct(NormalizedSales.invoice_number)
                   ).label('invoice_count'),
        func.coalesce(func.sum(case((NormalizedSales.payment_method == 'Cartão Multicaixa',
                      NormalizedSales.gross_amount), else_=0)), 0).label('card'),
    ).filter(func.to_char(NormalizedSales.date, 'MM') == month).first()

    vat_rows = db.query(
        NormalizedSales.vat_rate,
        func.coalesce(func.sum(NormalizedSales.vat_amount), 0).label('vat'),
    ).filter(func.to_char(NormalizedSales.date, 'MM') == month) \
     .group_by(NormalizedSales.vat_rate) \
     .order_by(NormalizedSales.vat_rate).all()

    top_prod = db.query(
        NormalizedSales.product,
        func.coalesce(func.sum(NormalizedSales.gross_amount), 0).label('g'),
    ).filter(func.to_char(NormalizedSales.date, 'MM') == month) \
     .group_by(NormalizedSales.product) \
     .order_by(func.sum(NormalizedSales.gross_amount).desc()).first()

    daily_peak = db.query(
        NormalizedSales.date,
        func.coalesce(func.sum(NormalizedSales.gross_amount), 0).label('g'),
    ).filter(func.to_char(NormalizedSales.date, 'MM') == month) \
     .group_by(NormalizedSales.date) \
     .order_by(func.sum(NormalizedSales.gross_amount).desc()).first()

    fees_total = float(sum(float(r.get('fees') or 0) for r in recon_rows))
    delta_sum = float(sum(float(r.get('delta') or 0) for r in recon_rows))

    gross = float(getattr(summary, 'gross', 0) or 0)
    card = float(getattr(summary, 'card', 0) or 0)
    card_share = (card / (gross or 1)) * 100.0

    return {
        'gross': gross,
        'vat': float(getattr(summary, 'vat', 0) or 0),
        'net': float(getattr(summary, 'net', 0) or 0),
        'invoice_count': int(getattr(summary, 'invoice_count', 0) or 0),
        'card': card,
        'card_share': card_share,
        'top_product': (top_prod.product if top_prod else 'N/A'),
        'peak_day': (daily_peak.date.isoformat() if daily_peak else 'N/A'),
        'peak_gross': float(getattr(daily_peak, 'g', 0) or 0),
        'fees_total': fees_total,
        'delta_sum': delta_sum,
        'vat_rows': [(float(v[0]), float(v[1])) for v in vat_rows],
    }


def monthly_report(db: Session, month: str, recon_rows: list[dict]):
    f = _facts(db, month, recon_rows)
    vat_breakdown = ', '.join(
        [f"{int(v[0])}%: {float(v[1]):.2f}" for v in f['vat_rows']])
    return REPORT_TEMPLATE.format(
        month=month,
        gross=f['gross'],
        vat=f['vat'],
        net=f['net'],
        card_share=f['card_share'],
        peak_day=f['peak_day'],
        peak_gross=f['peak_gross'],
        top_product=f['top_product'],
        delta_sum=f['delta_sum'],
        fees_total=f['fees_total'],
        invoice_count=f['invoice_count'],
        vat_breakdown=vat_breakdown,
    )

# Chat answer stub grounded: simply returns monthly report or clarifies delta explanation request


def answer(db: Session, month: str, question: str, recon_rows: list[dict]):
    q = (question or '').lower()
    f = _facts(db, month, recon_rows)

    # Intent: detailed VAT breakdown
    if 'vat' in q or 'iva' in q:
        parts = [f"{int(rate)}%: {amt:.2f}" for rate, amt in f['vat_rows']]
        if not parts:
            return f"No VAT data found for month {month}."
        return f"VAT breakdown for {month}: " + ', '.join(parts) + f". Total VAT: {f['vat']:.2f}."

    # Intent: card vs cash split
    if 'card' in q or 'cash' in q or 'multicaixa' in q:
        return (
            f"Card vs Cash ({month}): Card {f['card']:.2f} which is {f['card_share']:.2f}% of gross {f['gross']:.2f}."
        )

    # Intent: top product / top customer (we have only product here)
    if 'top product' in q or ('top' in q and 'product' in q):
        return f"Top product in {month}: {f['top_product']} with peak day {f['peak_day']} ({f['peak_gross']:.2f})."

    # Intent: peak day / daily max
    if 'peak' in q or ('max' in q and 'day' in q) or ('best' in q and 'day' in q):
        return f"Peak sales day in {month}: {f['peak_day']} with gross {f['peak_gross']:.2f}."

    # Intent: reconciliation delta explanation
    if ('why' in q or 'explain' in q) and 'delta' in q:
        largest = sorted(recon_rows, key=lambda r: abs(
            r['delta']), reverse=True)[:3]
        if not largest:
            return f"No reconciliation rows found for {month}."
        parts = [
            f"{r['date']}: delta {float(r['delta']):.2f} (fees {float(r['fees']):.2f}, bank {float(r['bank_tpa']):.2f})"
            for r in largest
        ]
        return "Reconciliation mismatches: " + '; '.join(parts)

    # Intent: general monthly report
    if 'report' in q or 'monthly' in q or 'summary' in q or 'overview' in q:
        return monthly_report(db, month, recon_rows)

    # Default: brief contextual response
    return (
        f"{month} summary: Gross {f['gross']:.2f}, VAT {f['vat']:.2f}, Net {f['net']:.2f}. "
        f"Card share {f['card_share']:.2f}%. Peak day {f['peak_day']} ({f['peak_gross']:.2f}). "
        f"Delta sum {f['delta_sum']:.2f}, fees total {f['fees_total']:.2f}."
    )
