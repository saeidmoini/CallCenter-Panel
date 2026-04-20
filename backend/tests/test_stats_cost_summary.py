from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.models.phone_number import CallStatus
from app.services import stats_service


class ScalarQuery:
    def __init__(self, value):
        self.value = value

    def filter(self, *args, **kwargs):
        return self

    def outerjoin(self, *args, **kwargs):
        return self

    def scalar(self):
        return self.value


class FakeDB:
    def __init__(self):
        self.values = iter([2, 640, 3, 1140])

    def query(self, *args, **kwargs):
        return ScalarQuery(next(self.values))


def test_cost_summary_uses_summed_scenario_rates(monkeypatch):
    fake_db = FakeDB()

    monkeypatch.setattr(
        stats_service,
        'ensure_config',
        lambda db, company_id=None: SimpleNamespace(cost_per_connected=500),
    )

    result = stats_service.cost_summary(fake_db, company_id=1)

    assert result['cost_per_connected'] == 500
    assert result['daily_count'] == 2
    assert result['daily_cost'] == 640
    assert result['monthly_count'] == 3
    assert result['monthly_cost'] == 1140
