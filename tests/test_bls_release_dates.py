from data.sources.bls import _estimate_us_cpi_release_date, _estimate_us_nfp_release_date


def test_estimate_cpi_release_date_for_dec_2025():
    assert _estimate_us_cpi_release_date("2025-12-01") == "2026-01-13"


def test_estimate_nfp_release_date_for_jan_2026():
    assert _estimate_us_nfp_release_date("2026-01-01") == "2026-02-06"
