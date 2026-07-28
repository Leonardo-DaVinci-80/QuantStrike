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
    def average_price(self) -> float: # returns avg historical price
        return mean(point.price for point in self.history)

    @property
    def median_price(self): # returns median historial price 
        return median(point.price for point in self.history)

    @property
    def standard_deviation(self): # return the standard deviation from the historical price
        if len(self.history) < 2:
            return 0.0
        return stdev(point.price for point in self.history)

    @property
    def total_return(self): # return the total percentage return over the dataset.
        first = self.history[0].price
        last = self.history[-1].price
        if first == 0:
            return 0.0
        return ((last - first) / first) * 100

    @property
    def daily_returns(self): # return the daily percentage returns.
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