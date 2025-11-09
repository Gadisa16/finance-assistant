from app.database import SessionLocal
from app.services.metrics import kpi_summary


def test_kpi_summary_no_data():
    db = SessionLocal()
    res = kpi_summary(db, '09')
    assert res is None or res.get('total_gross', 0) == 0
