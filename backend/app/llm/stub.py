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

# Chat answer stub grounded: intent-based responses kept minimal unless asked


def _is_greeting(q: str) -> bool:
    greetings = ['hi', 'hello', 'hey', 'ola', 'olá', 'oi',
                 'good morning', 'good afternoon', 'good evening']
    return any(q == g or q.startswith(g + ' ') for g in greetings)


def _mentions_vat(q: str) -> bool:
    return ('vat' in q) or ('iva' in q)


def _mentions_card_cash(q: str) -> bool:
    return ('card' in q) or ('cash' in q) or ('multicaixa' in q)


def _mentions_top_product(q: str) -> bool:
    return ('top product' in q) or ('top' in q and 'product' in q)


def _mentions_peak_day(q: str) -> bool:
    return ('peak' in q) or (('max' in q) and ('day' in q)) or (('best' in q) and ('day' in q))


def _mentions_recon_explain(q: str) -> bool:
    return (('why' in q) or ('explain' in q)) and ('delta' in q)


def _mentions_report(q: str) -> bool:
    return ('report' in q) or ('monthly' in q) or ('summary' in q) or ('overview' in q)


def _handle_greeting(month: str) -> str:
    return (f"Hi! I'm your finance assistant for {month}. "
            "Ask me about VAT, card vs cash, top products, peak day, or reconciliation.")


def _handle_vat(month: str, facts: dict) -> str:
    parts = [f"{int(rate)}%: {amt:.2f}" for rate, amt in facts['vat_rows']]
    if not parts:
        return f"No VAT data found for month {month}."
    return f"VAT breakdown for {month}: " + ', '.join(parts) + f". Total VAT: {facts['vat']:.2f}."


def _handle_card_cash(month: str, facts: dict) -> str:
    return (
        f"Card vs Cash ({month}): Card {facts['card']:.2f} which is {facts['card_share']:.2f}% of gross {facts['gross']:.2f}."
    )


def _handle_top_product(month: str, facts: dict) -> str:
    return f"Top product in {month}: {facts['top_product']} with peak day {facts['peak_day']} ({facts['peak_gross']:.2f})."


def _handle_peak_day(month: str, facts: dict) -> str:
    return f"Peak sales day in {month}: {facts['peak_day']} with gross {facts['peak_gross']:.2f}."


def _handle_recon_explain(month: str, recon_rows: list[dict]) -> str:
    largest = sorted(recon_rows, key=lambda r: abs(
        r['delta']), reverse=True)[:3]
    if not largest:
        return f"No reconciliation rows found for {month}."
    parts = [
        f"{r['date']}: delta {float(r['delta']):.2f} (fees {float(r['fees']):.2f}, bank {float(r['bank_tpa']):.2f})"
        for r in largest
    ]
    return "Reconciliation mismatches: " + '; '.join(parts)


def answer(db: Session, month: str, question: str, recon_rows: list[dict]):
    q = (question or '').lower().strip()
    facts = _facts(db, month, recon_rows)

    # Intent routing table to reduce branching complexity
    routes: list[tuple[callable, callable]] = [
        (_is_greeting, lambda: _handle_greeting(month)),
        (_mentions_vat, lambda: _handle_vat(month, facts)),
        (_mentions_card_cash, lambda: _handle_card_cash(month, facts)),
        (_mentions_top_product, lambda: _handle_top_product(month, facts)),
        (_mentions_peak_day, lambda: _handle_peak_day(month, facts)),
        (_mentions_recon_explain, lambda: _handle_recon_explain(month, recon_rows)),
        (_mentions_report, lambda: monthly_report(db, month, recon_rows)),
    ]

    for predicate, handler in routes:
        if predicate(q):
            return handler()

    # Default: brief contextual response — just a compact summary
    return (f"{month} summary available. Ask for VAT, card vs cash, top products, peak day, or a monthly report.")
