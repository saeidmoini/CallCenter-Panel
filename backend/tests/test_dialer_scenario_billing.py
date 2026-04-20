from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.models.phone_number import CallStatus, GlobalStatus
from app.services.dialer_service import report_result
from app.schemas.dialer import DialerReport


class FakeQuery:
    def __init__(self, first_result=None):
        self._first_result = first_result

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_result


class FakeDB:
    def __init__(self, *, number, batch_item, previous_call_result=None):
        self.number = number
        self.batch_item = batch_item
        self.previous_call_result = previous_call_result
        self.added = []
        self.commits = 0

    def get(self, model, ident):
        return self.number

    def add(self, obj):
        if getattr(obj, '__tablename__', None) == 'call_results':
            obj.id = 999
        self.added.append(obj)

    def flush(self):
        pass

    def commit(self):
        self.commits += 1

    def refresh(self, obj):
        pass

    def query(self, model):
        table = getattr(model, '__tablename__', '')
        if table == 'dialer_batch_items':
            return FakeQuery(self.batch_item)
        if table == 'call_results':
            return FakeQuery(self.previous_call_result)
        if table == 'schedule_configs':
            return FakeQuery(SimpleNamespace(wallet_balance=10_000, cost_per_connected=500, enabled=True, disabled_by_dialer=False, version=1))
        return FakeQuery(None)


def test_report_result_uses_batch_scenario_for_billing_when_report_scenario_missing(monkeypatch):
    company = SimpleNamespace(id=1, name='salehi')
    number = SimpleNamespace(
        id=10,
        phone_number='09120000000',
        global_status=GlobalStatus.ACTIVE,
        assigned_batch_id='batch-1',
        assigned_at=datetime.now(timezone.utc),
        last_called_at=None,
        last_called_company_id=None,
    )
    batch_item = SimpleNamespace(
        report_scenario_id=140,
        report_outbound_line_id=None,
        report_reason=None,
        reported_at=None,
        report_batch_id=None,
        report_call_result_id=None,
        report_attempted_at=None,
        report_status=None,
    )
    db = FakeDB(number=number, batch_item=batch_item)

    charged = {}

    monkeypatch.setattr('app.services.dialer_service._resolve_agent', lambda db, report, company: None)
    monkeypatch.setattr('app.services.dialer_service._sync_global_status_from_call_status', lambda number, status: None)
    monkeypatch.setattr('app.services.dialer_service.charge_for_connected_call', lambda db, company_id=None, scenario_id=None: charged.setdefault('scenario_id', scenario_id))

    report = DialerReport(
        number_id=number.id,
        phone_number=number.phone_number,
        company=company.name,
        scenario_id=None,
        outbound_line_id=None,
        status=CallStatus.CONNECTED,
        reason=None,
        attempted_at=datetime.now(timezone.utc),
        call_allowed=None,
        agent_id=None,
        agent_phone=None,
        user_message=None,
        batch_id='batch-1',
    )

    result = report_result(db, report, company)

    created_call = next(obj for obj in db.added if getattr(obj, '__tablename__', None) == 'call_results')

    assert result['id'] == number.id
    assert created_call.scenario_id == 140
    assert batch_item.report_scenario_id == 140
    assert charged['scenario_id'] == 140
