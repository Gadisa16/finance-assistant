# Finance Assistant

A full‑stack Finance Assistant that ingests monthly Sales (Excel) and Bank (PDF) files, normalizes the data into PostgreSQL, computes KPIs/VAT, reconciles card sales vs bank TPA credits, and provides a grounded chat experience powered by Groq (or a local stub fallback).

## Features

- Upload: Excel (sales) + PDF (bank) for a selected month, with month mismatch validation
- KPIs: Gross, Net, VAT, Card vs Cash, Daily trend chart
- VAT report: Breakdown by VAT rate
- Reconciliation: Daily Card sales vs FECHO_TPA bank credits, with deltas and totals; paginated view
- Top lists: Top products and top customers
- Chat: Grounded Q&A over the selected month’s facts; Groq/OpenAI-compatible or local stub
- Typed frontend (React + TypeScript) and FastAPI backend (SQLAlchemy + Alembic)

## Architecture

- Frontend: React + Vite + TypeScript + Tailwind
- Backend: FastAPI + SQLAlchemy + Alembic + pdfplumber/pandas + httpx
- Database: PostgreSQL (Dockerized)
- LLM: Groq via OpenAI-compatible API (optional). If no LLM configured, a deterministic local stub answers based on computed facts.

Repo layout:

```
finance-assistant/
  backend/
    app/                # FastAPI app
    migrations/         # Alembic migrations
  frontend/             # React + Vite app
  docker-compose.yml
```

## Quick start (Docker)

Prerequisites: Docker Desktop with Docker Compose

1. Optional: create a `.env` file in the project root (same folder as `docker-compose.yml`) if you want Groq chat:

```
LLM_API_URL=https://api.groq.com/openai/v1
LLM_API_KEY=your_groq_api_key
LLM_MODEL=llama-3.3-70b-versatile
```

If you don’t provide these, the app uses a local stub and still works, but not effective.

2. Start the stack (backend, frontend, db):

```bash
docker compose up --build -d
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (FastAPI docs at /docs)
- Postgres: exposed at 5432 (internal service `db`)

To follow logs: `docker compose logs -f`. To stop everything: `docker compose down`.

3. Migrations: automatically applied on backend startup (first start may take a few seconds). No manual step needed.

4. Verify services:

- Frontend: http://localhost:5173
- Backend API & docs: http://localhost:8000/docs
- Database (internal service): `db` on port 5432

5. Upload your month files:

- In the UI: open the Upload panel, pick month (MM), then select Sales Excel and Bank PDF.
- Or via curl (example for September):

```bash
curl -X POST "http://localhost:8000/files/upload?month=09" \
  -H "accept: application/json" -H "Content-Type: multipart/form-data" \
  -F "sales_excel=@VENDAS SETEMBRO.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
  -F "bank_pdf=@Extracto Bai 02 - Setembro 2025.pdf;type=application/pdf"
```

## Configuration

- Frontend base URL: `frontend/.env` (`VITE_API_URL`) defaults to `http://localhost:8000` for host-browser development
- Backend environment (read by `backend/app/config.py`):
  - `DATABASE_URL` (default connects to dockerized Postgres)
  - `LLM_API_URL` (set to Groq’s `https://api.groq.com/openai/v1` to enable real LLM)
  - `LLM_API_KEY` (Groq API key)
  - `LLM_MODEL` (default `llama-3.3-70b-versatile`)
  - `UPLOAD_DIR` (default `/data/uploads` mapped to a volume)

Security note: Keep LLM credentials on the backend side (compose environment). Do not place API keys in `frontend/.env` since that is served to the browser.

## Using the app

1. Choose a month in the Dashboard dropdown (MM format)
2. Click the Upload panel (top-right widget), select the Sales Excel and Bank PDF, then upload. The server validates the month and ingests data.
3. Explore KPIs, Daily chart, VAT report, Top lists, and Reconciliation (paginated by 10 rows, totals always visible)
4. Chat (bottom-right): ask questions about the selected month. If Groq is configured, answers come from `LLM_MODEL` grounded by real metrics; otherwise a local stub answers with computed facts.

## API endpoints (brief)

- `GET /kpi/summary?month=MM` — totals (gross/net/vat/card/cash)
- `GET /kpi/daily?month=MM` — daily gross/card/cash
- `GET /kpi/top-products?month=MM&limit=10`
- `GET /kpi/top-customers?month=MM&limit=10`
- `GET /vat/report?month=MM`
- `GET /recon/card?month=MM` — reconciliation rows
- `POST /files/upload?month=MM` — multipart form: `sales_excel`, `bank_pdf`
- `POST /chat/ask` — body: `{ month, question }`

## Local development (optional)

If you prefer to run services locally without containers:

- Backend (from `backend/`):
  - Create and activate a venv, then:
  - `pip install -r requirements.txt`
  - `alembic upgrade head` (if needed)
  - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Frontend (from `frontend/`):
  - `npm install`
  - `npm run dev` (Vite at http://localhost:5173)
  - Ensure `frontend/.env` has `VITE_API_URL=http://localhost:8000`

## Troubleshooting

- “relation \"normalized_sales\" does not exist” during upload: migrations may not have completed yet. Wait a few seconds and check `docker compose logs -f backend`. If needed, run manually: `docker compose run --rm backend alembic upgrade head` then `docker compose restart backend`.
- Upload fails quickly: large files may need time; backend upload timeout is extended; try again and check backend logs.
- Month returns no data: confirm the month in the dropdown matches the data month; the backend rejects mismatched uploads.
- Chat returns a “[LLM unavailable]” summary: verify Groq env vars and connectivity; otherwise the stub still responds using computed metrics.
- Frontend cannot reach backend in Docker: verify `VITE_API_URL` is `http://localhost:8000` since the browser runs on the host.

## Resetting data

- Wipe everything (DB + uploads volume):

```bash
docker compose down -v
docker compose up --build -d
```

- Keep containers and just clear tables (inside Postgres):

```sql
TRUNCATE normalized_sales RESTART IDENTITY CASCADE;
TRUNCATE bank_tpa RESTART IDENTITY CASCADE;
```

## How migrations run

Migrations are applied automatically by the backend on startup (`alembic upgrade head` before launching the API). If you want to switch to manual control (e.g., in local dev), change the backend command to start Uvicorn directly and run Alembic yourself.
