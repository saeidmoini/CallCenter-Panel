import pytest

from app.services.wallet_service import (
    parse_bank_sms,
    build_utc_datetime_from_jalali_minute,
    should_store_bank_sms,
)
from app.services.schedule_service import TEHRAN_TZ


def test_parse_bank_sms_credit_sample():
    sample = "362970014368052001\n70,000,000+\n1404/11/13-14:03\nمانده:70,694,954"
    parsed, error = parse_bank_sms(sample)
    assert error is None
    assert parsed is not None
    assert parsed.amount_rial == 70_000_000
    assert parsed.amount_toman == 7_000_000
    assert parsed.is_credit is True
    tehran_dt = parsed.transaction_at_utc.astimezone(TEHRAN_TZ)
    assert parsed.transaction_at_utc.tzinfo is not None
    assert tehran_dt.hour == 14
    assert tehran_dt.minute == 3


def test_parse_bank_sms_debit_is_not_credit():
    sample = "20,000,000-\n1404/11/13-08:10"
    parsed, error = parse_bank_sms(sample)
    assert error is None
    assert parsed is not None
    assert parsed.is_credit is False
    assert should_store_bank_sms(parsed) is False


def test_parse_bank_sms_requires_amount_sign():
    parsed, error = parse_bank_sms("1404/11/13-14:03\nبدون مبلغ")
    assert parsed is None
    assert error == "amount_sign_not_found"
    assert should_store_bank_sms(parsed) is False


def test_should_store_bank_sms_credit_only():
    sample = "70,000,000+\n1404/11/13-14:03"
    parsed, error = parse_bank_sms(sample)
    assert error is None
    assert parsed is not None
    assert should_store_bank_sms(parsed) is True


def test_build_utc_datetime_from_jalali_minute_validation():
    with pytest.raises(ValueError):
        build_utc_datetime_from_jalali_minute("1404-11-13", 14, 3)
    with pytest.raises(ValueError):
        build_utc_datetime_from_jalali_minute("1404/11/13", 24, 0)
    with pytest.raises(ValueError):
        build_utc_datetime_from_jalali_minute("1404/11/13", 23, 60)
