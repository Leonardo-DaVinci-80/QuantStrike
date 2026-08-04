from datetime import timedelta
from typing import List
from backend.models.price_point import PricePoint
from statistics import mean, median, stdev


class MarketMetrics:
    def __init__(self, history: List[PricePoint]):
        if not history:
            raise ValueError("Price history cannot be empty.")

        self.history = sorted(history, key=lambda p: p.timestamp)

    @property
    def current_date(self):
        return self.history[-1].timestamp

    @property
    def current_price(self) -> float:
        return self.history[-1].price

    @property
    def daily_change(self) -> float:
        if len(self.history) < 2:
            return 0.0
        return self.history[-1].price - self.history[-2].price

    @property
    def daily_change_percent(self) -> float:
        if len(self.history) < 2:
            return 0.0
        yesterday = self.history[-2].price
        if yesterday == 0:
            return 0.0
        return (self.daily_change / yesterday) * 100

    @property
    def all_time_high(self) -> float:
        return max(point.price for point in self.history)

    @property
    def all_time_low(self) -> float:
        return min(point.price for point in self.history)

    @property
    def high_52w(self) -> float:
        cutoff = self.history[-1].timestamp - timedelta(days=365)
        prices = [
            point.price
            for point in self.history
            if point.timestamp >= cutoff
        ]
        return max(prices)

    @property
    def low_52w(self) -> float:
        cutoff = self.history[-1].timestamp - timedelta(days=365)
        prices = [
            point.price
            for point in self.history
            if point.timestamp >= cutoff
        ]
        return min(prices)

    @property
    def average_price(self) -> float:
        return mean(point.price for point in self.history)

    @property
    def median_price(self):
        return median(point.price for point in self.history)

    @property
    def standard_deviation(self):
        if len(self.history) < 2:
            return 0.0
        return stdev(point.price for point in self.history)

    @property
    def total_return(self):
        first = self.history[0].price
        last = self.history[-1].price
        if first == 0:
            return 0.0
        return ((last - first) / first) * 100

    @property
    def daily_returns(self):
        returns = []
        for previous, current in zip(self.history, self.history[1:]):
            if previous.price == 0:
                continue
            change = (
                (current.price - previous.price)
                / previous.price
            ) * 100
            returns.append(change)
        return returns

    def _return_over_days(self, days: int) -> float:
        cutoff = self.current_date - timedelta(days=days)
        past_points = [p for p in self.history if p.timestamp <= cutoff]
        if not past_points:
            return 0.0
        past_price = past_points[-1].price
        if past_price == 0:
            return 0.0
        return ((self.current_price - past_price) / past_price) * 100

    @property
    def weekly_return(self) -> float:
        return self._return_over_days(7)

    @property
    def monthly_return(self) -> float:
        return self._return_over_days(30)

    @property
    def annual_return(self) -> float:
        return self._return_over_days(365)

    @property
    def cagr(self) -> float:
        first = self.history[0]
        last = self.history[-1]
        if first.price <= 0:
            return 0.0
        years = (last.timestamp - first.timestamp).days / 365.25
        if years <= 0:
            return 0.0
        return ((last.price / first.price) ** (1 / years) - 1) * 100

    @property
    def volatility(self) -> float:
        returns = self.daily_returns
        if len(returns) < 2:
            return 0.0
        return stdev(returns)

    def moving_average(self, window: int) -> float:
        if len(self.history) < window:
            prices = [p.price for p in self.history]
        else:
            prices = [p.price for p in self.history[-window:]]
        return mean(prices)

    @property
    def max_drawdown(self) -> float:
        peak = self.history[0].price
        max_dd = 0.0
        for point in self.history:
            if point.price > peak:
                peak = point.price
            if peak > 0:
                drawdown = (point.price - peak) / peak * 100
                if drawdown < max_dd:
                    max_dd = drawdown
        return max_dd