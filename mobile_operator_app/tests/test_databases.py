import pytest
from datetime import date, timedelta
from databases.models import Subscriber, DebtorReport


# --- Тести для Subscriber ---

def test_subscriber_total_cost():
    """Перевірка обчислення повної вартості контракту"""
    sub = Subscriber(
        ric="RIC-123",
        pin_code="0000",
        full_name="Test User",
        phone_model="iPhone",
        phone_type="Smartphone",
        service_type="Premium",
        contract_start_date=date.today(),
        contract_duration_months=12,
        monthly_fee=100.0,
        is_active=True
    )
    # 12 місяців * 100 грн = 1200
    assert sub.total_cost == 1200.0


# --- Тести для DebtorReport ---

def test_debt_calculation_no_overdue():
    """Якщо оплата була сьогодні, боргу немає"""
    report = DebtorReport(
        ric="RIC-1",
        full_name="User",
        monthly_fee=100.0,
        last_payment_date=date.today()
    )
    assert report.days_overdue == 0
    assert report.debt_amount == 0.0


def test_debt_calculation_one_month_overdue():
    """Прострочка 35 днів = борг за 2 місяці (округлення вгору)"""
    # 35 днів тому
    past_date = date.today() - timedelta(days=35)

    report = DebtorReport(
        ric="RIC-2",
        full_name="Debtor",
        monthly_fee=150.0,
        last_payment_date=past_date
    )

    assert report.days_overdue == 35
    # 35 днів / 30 = 1.16
    # 2 * 150 = 300 грн боргу
    assert report.debt_amount == 300.0


def test_debt_calculation_no_payment_date():
    report = DebtorReport(
        ric="RIC-3",
        full_name="New User",
        monthly_fee=100.0,
        last_payment_date=None
    )
    assert report.days_overdue == 0
    assert report.debt_amount == 0.0