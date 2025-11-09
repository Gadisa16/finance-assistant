import pandas as pd
import pdfplumber
from datetime import datetime, date
from typing import List, Dict, Any
import re
import json
from ..models.models import BankTx, NormalizedSales, RawSales
from ..database import SessionLocal

CARD_KEY = "Fecho TPA"
COMISSAO_KEY = "Comissão"
IVA_COMISSAO_KEY = "IVA s/Comissão"

VAT_RATES_ALLOWED = {0, 5, 7, 14}

excel_col_map = {
    'Documento': 'documento',
    'NºDoc.': 'numero',
    'Data Emissão': 'data_emissao',
    'Código Artigo': 'codigo_artigo',
    'Artigo': 'artigo',
    'Quantidade': 'quantidade',
    'Preço Unit. s/Imp': 'preco_unit_net',
    'Imposto': 'imposto',
    'Total Bruto': 'total_bruto',
    'Tipo Pagamento': 'tipo_pagamento'
}

DATE_CACHE = {}


def excel_serial_to_date(v: float) -> date:
    # Excel serial (assuming 1900-based)
    if v in DATE_CACHE:
        return DATE_CACHE[v]
    base = datetime(1899, 12, 30)  # Excel's 1 -> 1899-12-31
    d = base + pd.to_timedelta(v, unit='D')
    DATE_CACHE[v] = d.date()
    return d.date()


def parse_excel(path: str, month: str) -> Dict[str, Any]:
    df = pd.read_excel(
        path, sheet_name='Detalhes de Documentos Emitidos', engine='openpyxl')
    df = df.rename(
        columns={k: v for k, v in excel_col_map.items() if k in df.columns})
    rows = []
    for _, r in df.iterrows():
        try:
            raw_date = r.get('data_emissao')
            if pd.isna(raw_date):
                continue
            dt = excel_serial_to_date(raw_date) if isinstance(
                raw_date, (int, float)) else pd.to_datetime(raw_date).date()
            if month and dt.strftime('%m') != month:
                continue
            vat_rate = float(r.get('imposto', 0))
            if vat_rate not in VAT_RATES_ALLOWED:
                vat_rate = 14.0 if vat_rate > 0 else 0.0
            quantity = float(r.get('quantidade', 1) or 1)
            unit_net = float(r.get('preco_unit_net', 0))
            net_amount = round(unit_net * quantity, 2)
            vat_amount = round(net_amount * (vat_rate/100.0), 2)
            gross_amount = round(net_amount + vat_amount, 2)
            line = {
                'date': dt,
                'invoice_number': str(r.get('numero') or r.get('documento')),
                'customer': 'Consumidor Final',
                'product': str(r.get('artigo')),
                'quantity': quantity,
                'unit_price_net': unit_net,
                'vat_rate': vat_rate,
                'net_amount': net_amount,
                'vat_amount': vat_amount,
                'gross_amount': gross_amount,
                'payment_method': str(r.get('tipo_pagamento'))
            }
            rows.append(line)
        except Exception:
            continue
    return {'normalized': rows, 'raw_count': len(df)}


bank_patterns = [
    (re.compile(r'Fecho TPA'), 'FECHO_TPA'),
    (re.compile(r'Comissão.*STC', re.IGNORECASE), 'COMISSAO_STC'),
    (re.compile(r'IVA s/Comissão', re.IGNORECASE), 'IVA_COMISSAO'),
    (re.compile(r'Transf interna', re.IGNORECASE), 'TRANSF_INTERNA'),
    (re.compile(r'Reserva', re.IGNORECASE), 'RESERVA')
]

DATE_REGEX = re.compile(r'(\d{2}[-/]\d{2}[-/]\d{4})')

# Simple PDF line parser; real life would require table extraction per page


def parse_bank_pdf(path: str, month: str) -> List[Dict[str, Any]]:
    out = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ''
            for line in text.split('\n'):
                if not line.strip():
                    continue
                m = DATE_REGEX.search(line)
                if not m:
                    continue
                dt = datetime.strptime(m.group(1), '%d-%m-%Y').date()
                if month and dt.strftime('%m') != month:
                    continue
                # crude splitting for amounts
                parts = line.split()
                description = ' '.join(parts[1:-3]) if len(parts) > 4 else line
                try:
                    debit = None
                    credit = None
                    balance = None
                    # last three tokens guess
                    maybe_vals = parts[-3:]
                    nums = []
                    for v in maybe_vals:
                        v2 = v.replace('.', '').replace(',', '.')
                        try:
                            nums.append(float(v2))
                        except ValueError:
                            nums.append(None)
                    if len(nums) == 3:
                        debit, credit, balance = nums
                    tx_type = 'OTHER'
                    for patt, label in bank_patterns:
                        if patt.search(line):
                            tx_type = label
                            break
                    out.append({
                        'date': dt,
                        'description': description,
                        'debit': debit,
                        'credit': credit,
                        'balance': balance,
                        'tx_type': tx_type
                    })
                except Exception:
                    continue
    return out


def ingest_files(excel_path: str, pdf_path: str, month: str):
    db = SessionLocal()
    excel_res = parse_excel(excel_path, month)
    bank_rows = parse_bank_pdf(pdf_path, month)
    # store raw and normalized
    raw_record = RawSales(source=excel_path, raw_json=json.dumps(
        {'raw_count': excel_res['raw_count']}))
    db.add(raw_record)
    for line in excel_res['normalized']:
        db.add(NormalizedSales(**line))
    for b in bank_rows:
        db.add(BankTx(**b))
    db.commit()
    return len(excel_res['normalized']), len(bank_rows)
