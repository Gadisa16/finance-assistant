from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.sql import case
import httpx

from ..models.models import NormalizedSales
from ..config import settings


def _month_filter(month: str):
    return func.to_char(NormalizedSales.date, 'MM') == month


def _collect_facts(db: Session, month: str, recon_rows: List[Dict]):
    card_case = case((NormalizedSales.payment_method ==
                     'Cartão Multicaixa', NormalizedSales.gross_amount), else_=0)

    summary = (
        db.query(
            func.coalesce(func.sum(NormalizedSales.gross_amount),
                          0).label('gross'),
            func.coalesce(func.sum(NormalizedSales.vat_amount),
                          0).label('vat'),
            func.coalesce(func.sum(NormalizedSales.net_amount),
                          0).label('net'),
            func.coalesce(func.sum(card_case), 0).label('card'),
        )
        .filter(_month_filter(month))
        .first()
    )

    vat_rows = (
        db.query(
            NormalizedSales.vat_rate,
            func.coalesce(func.sum(NormalizedSales.vat_amount),
                          0).label('vat'),
        )
        .filter(_month_filter(month))
        .group_by(NormalizedSales.vat_rate)
        .order_by(NormalizedSales.vat_rate)
        .all()
    )

    top_prod = (
        db.query(NormalizedSales.product, func.coalesce(
            func.sum(NormalizedSales.gross_amount), 0).label('g'))
        .filter(_month_filter(month))
        .group_by(NormalizedSales.product)
        .order_by(func.sum(NormalizedSales.gross_amount).desc())
        .first()
    )

    daily_peak = (
        db.query(NormalizedSales.date, func.coalesce(
            func.sum(NormalizedSales.gross_amount), 0).label('g'))
        .filter(_month_filter(month))
        .group_by(NormalizedSales.date)
        .order_by(func.sum(NormalizedSales.gross_amount).desc())
        .first()
    )

    fees_total = float(sum(float(r.get('fees') or 0) for r in recon_rows))
    delta_sum = float(sum(float(r.get('delta') or 0) for r in recon_rows))

    facts = {
        'month': month,
        'gross': float(getattr(summary, 'gross', 0) or 0),
        'vat': float(getattr(summary, 'vat', 0) or 0),
        'net': float(getattr(summary, 'net', 0) or 0),
        'card': float(getattr(summary, 'card', 0) or 0),
        'card_share_pct': round((float(getattr(summary, 'card', 0) or 0) / (float(getattr(summary, 'gross', 0) or 1))) * 100, 2),
        'peak_day': (daily_peak.date.isoformat() if daily_peak else 'N/A'),
        'peak_gross': float(getattr(daily_peak, 'g', 0) or 0),
        'top_product': (top_prod.product if top_prod else 'N/A'),
        'fees_total': fees_total,
        'delta_sum': delta_sum,
        'vat_rows': [(float(v[0]), float(v[1])) for v in vat_rows],
    }
    return facts


async def _call_openai_compatible(model: str, system_prompt: str, user_prompt: str) -> str:
    url = settings.llm_api_url.rstrip('/') + '/chat/completions' if settings.llm_api_url.endswith(
        '/v1') or settings.llm_api_url.endswith('/openai/v1') or settings.llm_api_url.endswith('/v1/') else settings.llm_api_url.rstrip('/')
    headers = {
        'Authorization': f'Bearer {settings.llm_api_key or ""}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': model,
        'temperature': 0.2,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data['choices'][0]['message']['content']


def format_facts_as_text(facts: Dict) -> str:
    vat_text = ', '.join(
        [f"{int(r[0])}% VAT={r[1]:.2f}" for r in facts['vat_rows']]) or 'none'
    return (
        f"Month: {facts['month']}\n"
        f"Gross: {facts['gross']:.2f}, VAT: {facts['vat']:.2f}, Net: {facts['net']:.2f}\n"
        f"Card: {facts['card']:.2f} ({facts['card_share_pct']:.2f}%), Peak Day: {facts['peak_day']} ({facts['peak_gross']:.2f})\n"
        f"Top Product: {facts['top_product']}\n"
        f"Reconciliation: delta_sum={facts['delta_sum']:.2f}, fees_total={facts['fees_total']:.2f}\n"
        f"VAT breakdown: {vat_text}"
    )


async def answer_groq(db: Session, month: str, question: str, recon_rows: List[Dict]) -> str:
    facts = _collect_facts(db, month, recon_rows)
    # If no sales data, short-circuit with grounded reply
    if facts['gross'] == 0 and facts['net'] == 0:
        return "No sales data found for the selected month. Please upload the Excel/PDF and try again."

    system = (
        "You are a finance analyst. Only answer using the facts provided. "
        "If a value is missing, say you don't have that data. Keep answers concise (8–12 sentences)."
    )
    user = (
        f"Question: {question}\n\n"
        f"Facts (ground truth):\n{format_facts_as_text(facts)}\n\n"
        "Explain reconciliation mismatches if delta_sum != 0 by referencing fees and days."
    )
    # Choose model from settings (backend env), defaulting to Groq's recommended 70B versatile
    model = getattr(settings, 'llm_model', None) or 'llama-3.3-70b-versatile'
    try:
        return await _call_openai_compatible(model, system, user)
    except Exception:
        # Fallback: return a concise grounded summary
        return (
            f"[LLM unavailable] Grounded summary for {facts['month']}: Gross {facts['gross']:.2f}, "
            f"VAT {facts['vat']:.2f}, Net {facts['net']:.2f}, Card share {facts['card_share_pct']:.2f}%. "
            f"Peak day {facts['peak_day']} at {facts['peak_gross']:.2f}. "
            f"Reconciliation delta sum {facts['delta_sum']:.2f}, fees total {facts['fees_total']:.2f}."
        )
