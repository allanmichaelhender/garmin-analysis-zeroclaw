"""Changepoint Detection service for workout interval segmentation."""

import logging
import numpy as np
import ruptures as rpt
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ChangepointDetector:
    """Detects intervals in workout data using changepoint detection."""

    def __init__(self, penalty: float = 5.0, model: str = "rbf"):
        """
        Initialize changepoint detector.

        Args:
            penalty: Sensitivity parameter. Higher = fewer intervals
            model: Detection model ('rbf', 'linear', 'normal', etc.)
        """
        self.penalty = penalty
        self.model = model

    def detect_intervals(
        self,
        signal: np.ndarray,
        timestamps: Optional[np.ndarray] = None,
        min_interval_length: int = 30
    ) -> List[Dict]:
        """
        Detect intervals in workout data.

        Args:
            signal: 1D or 2D array of workout data (e.g., heart rate)
            timestamps: Optional array of timestamps for each data point
            min_interval_length: Minimum number of data points per interval

        Returns:
            List of interval dictionaries with start, end, and stats
        """
        try:
            # Ensure signal is numpy array
            signal = np.array(signal)

            # Handle 1D vs 2D signals
            if len(signal.shape) == 1:
                signal = signal.reshape(-1, 1)

            # Run PELT algorithm
            algo = rpt.Pelt(model=self.model).fit(signal)
            breakpoints = algo.predict(pen=self.penalty)

            # Remove the last breakpoint (it's the end of the data)
            if breakpoints and breakpoints[-1] == len(signal):
                breakpoints = breakpoints[:-1]

            # Filter by minimum interval length
            filtered_breakpoints = []
            prev_break = 0
            for break_idx in breakpoints:
                if break_idx - prev_break >= min_interval_length:
                    filtered_breakpoints.append(break_idx)
                    prev_break = break_idx
                else:
                    # Merge this interval with the previous one
                    prev_break = break_idx

            # Extract intervals
            intervals = []
            start_idx = 0

            for end_idx in filtered_breakpoints + [len(signal)]:
                segment = signal[start_idx:end_idx]

                interval = {
                    "start_idx": start_idx,
                    "end_idx": end_idx,
                    "duration_samples": end_idx - start_idx,
                    "mean": float(np.mean(segment)),
                    "std": float(np.std(segment)),
                    "min": float(np.min(segment)),
                    "max": float(np.max(segment)),
                    "median": float(np.median(segment)),
                }

                # Add timestamps if provided
                if timestamps is not None:
                    interval["start_time"] = float(timestamps[start_idx])
                    interval["end_time"] = float(timestamps[end_idx - 1])
                    interval["duration_seconds"] = interval["end_time"] - interval["start_time"]

                intervals.append(interval)
                start_idx = end_idx

            logger.info(f"Detected {len(intervals)} intervals with {len(filtered_breakpoints)} breakpoints")
            return intervals

        except Exception as e:
            logger.error(f"Failed to detect intervals: {e}")
            return []

    def detect_multivariate_intervals(
        self,
        signals: Dict[str, np.ndarray],
        timestamps: Optional[np.ndarray] = None,
        min_interval_length: int = 30
    ) -> List[Dict]:
        """
        Detect intervals using multiple signals simultaneously.

        Args:
            signals: Dictionary of signal arrays (e.g., {'heart_rate': [...], 'cadence': [...]})
            timestamps: Optional array of timestamps
            min_interval_length: Minimum number of data points per interval

        Returns:
            List of interval dictionaries with stats for each signal
        """
        try:
            # Stack signals into 2D array
            signal_names = list(signals.keys())
            signal_matrix = np.column_stack([signals[name] for name in signal_names])

            # Detect intervals
            base_intervals = self.detect_intervals(
                signal_matrix,
                timestamps=timestamps,
                min_interval_length=min_interval_length
            )

            # Add signal-specific stats to each interval
            for interval in base_intervals:
                start_idx = interval["start_idx"]
                end_idx = interval["end_idx"]

                for signal_name in signal_names:
                    segment = signals[signal_name][start_idx:end_idx]
                    interval[f"{signal_name}_mean"] = float(np.mean(segment))
                    interval[f"{signal_name}_std"] = float(np.std(segment))
                    interval[f"{signal_name}_min"] = float(np.min(segment))
                    interval[f"{signal_name}_max"] = float(np.max(segment))

            return base_intervals

        except Exception as e:
            logger.error(f"Failed to detect multivariate intervals: {e}")
            return []

    def smooth_signal(self, signal: np.ndarray, window_size: int = 5) -> np.ndarray:
        """
        Apply moving average smoothing to reduce noise.

        Args:
            signal: Input signal array
            window_size: Size of moving average window

        Returns:
            Smoothed signal array
        """
        try:
            if len(signal) < window_size:
                return signal

            # Use pandas rolling mean for efficient smoothing
            import pandas as pd
            series = pd.Series(signal)
            smoothed = series.rolling(window=window_size, center=True).mean()

            # Fill NaN values at edges with original values
            smoothed = smoothed.fillna(series)

            return smoothed.values

        except Exception as e:
            logger.error(f"Failed to smooth signal: {e}")
            return signal
