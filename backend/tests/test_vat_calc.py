from app.services.parsing import excel_serial_to_date


def test_excel_serial_to_date():
    # Excel serial for 2025-09-01 roughly
    d = excel_serial_to_date(45930)
    assert d.year == 2025 and d.month == 9
