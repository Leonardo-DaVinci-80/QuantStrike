from dataclasses import dataclass
from typing import List

import numpy as np

from backend.models.price_point import PricePoint


@dataclass
class CleanResult:
    accepted: List[PricePoint]
    suspicious: List[PricePoint]
    rejected: List[PricePoint]


class PriceCleaner:
    """
    Robust sequential price cleaner.

    Raw observations are never modified.
    Observations are classified as accepted, suspicious, or rejected.
    """

    def __init__(
        self,
        window=60,
        min_history=30,
        z_threshold=5.0,
    ):
        self.window = window
        self.min_history = min_history
        self.z_threshold = z_threshold

    def clean(
        self,
        history: List[PricePoint],
    ) -> CleanResult:

        if not history:
            return CleanResult([], [], [])

        history = sorted(
            history,
            key=lambda p: p.timestamp
        )

        accepted = [history[0]]
        suspicious = []
        rejected = []

        returns = []

        for point in history[1:]:

            previous = accepted[-1]

            if previous.price <= 0:
                accepted.append(point)
                continue

            current_return = (
                point.price / previous.price
            ) - 1

            # Not enough historical observations yet.
            if len(returns) < self.min_history:
                accepted.append(point)
                returns.append(current_return)
                continue

            recent_returns = np.array(
                returns[-self.window:],
                dtype=float
            )

            median = np.median(recent_returns)

            deviations = np.abs(
                recent_returns - median
            )

            mad = np.median(deviations)

            # Robust z-score.
            if mad > 0:
                robust_z = (
                    0.6745
                    * (current_return - median)
                    / mad
                )

            else:
                std = np.std(recent_returns)

                if std > 0:
                    robust_z = (
                        current_return - median
                    ) / std
                else:
                    robust_z = 0.0

            # Extremely unusual movement.
            if abs(robust_z) > self.z_threshold:

                # Look ahead for a possible reversion.
                # We cannot know the future here, so initially
                # classify as suspicious rather than immediately
                # deleting the observation.
                suspicious.append(point)

                continue

            accepted.append(point)
            returns.append(current_return)

        return CleanResult(
            accepted=accepted,
            suspicious=suspicious,
            rejected=rejected,
        )