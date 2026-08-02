from datetime import datetime

from backend.models.price_point import PricePoint
from backend.analytics.market_metrics import MarketMetrics


def create_test_history():
    return [
        PricePoint(
            timestamp=datetime(2025, 1, 1),
            price=10
        ),
        PricePoint(
            timestamp=datetime(2025, 1, 2),
            price=12
        ),
        PricePoint(
            timestamp=datetime(2025, 1, 3),
            price=15
        ),
    ]


def test_current_price():
    metrics = MarketMetrics(create_test_history())

    assert metrics.current_price == 15


def test_daily_change():
    metrics = MarketMetrics(create_test_history())

    assert metrics.daily_change == 3


def test_daily_change_percent():
    metrics = MarketMetrics(create_test_history())

    assert metrics.daily_change_percent == 25


def test_all_time_high():
    metrics = MarketMetrics(create_test_history())

    assert metrics.all_time_high == 15


def test_all_time_low():
    metrics = MarketMetrics(create_test_history())

    assert metrics.all_time_low == 10