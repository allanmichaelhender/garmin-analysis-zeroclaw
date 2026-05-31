"""Visual HR Profile Analysis — sends HR plots to Anthropic Claude for AI-driven analysis."""

import logging

logger = logging.getLogger(__name__)


class HRProfileAnalyzer:
    """Analyses heart rate profiles by generating plots and sending them to Anthropic Claude
    for visual interpretation — no algorithmic changepoint detection needed."""

    def __init__(self):
        logger.info("HRProfileAnalyzer initialized — uses Claude visual analysis for HR profiling")

    # Interval detection is now performed visually by Anthropic Claude.
    # The analyze_hr_profile MCP tool generates an HR plot with workout splits
    # and sends it to Claude, which returns a structured narrative describing
    # warmup, steady-state, interval, and cooldown phases.
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
