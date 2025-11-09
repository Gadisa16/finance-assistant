from app.services.parsing import VAT_RATES_ALLOWED


def test_vat_rates_allowed():
    assert set(VAT_RATES_ALLOWED) == {0, 5, 7, 14}
