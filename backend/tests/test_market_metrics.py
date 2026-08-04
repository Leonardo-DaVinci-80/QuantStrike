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

def test_cagr():
    metrics = MarketMetrics(create_test_history())
    assert metrics.cagr != 0.0  # just confirms it computes without error

def test_volatility():
    metrics = MarketMetrics(create_test_history())
    assert metrics.volatility >= 0.0

def test_max_drawdown():
    metrics = MarketMetrics(create_test_history()) # test data is monotonically increasing, so drawdown should be 0
    assert metrics.max_drawdown == 0.0

def test_moving_average():
    metrics = MarketMetrics(create_test_history())
    assert metrics.moving_average(2) == (12 + 15) / 2