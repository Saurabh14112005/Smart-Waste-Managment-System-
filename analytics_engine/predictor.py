class OverflowPredictor:
    """
    Deterministic time-to-threshold from current fill and assumed average fill rate.
    No random numbers — tune fill_rate_per_hour from your fleet / historical studies.
    """

    def predict_overflow_time(self, current_level: int, fill_rate_per_hour: float = 5.0, threshold: int = 95) -> float:
        if current_level >= threshold:
            return 0.0
        remaining = threshold - current_level
        if fill_rate_per_hour <= 0:
            return float("inf")
        return round(remaining / fill_rate_per_hour, 2)

    def get_forecast(self, bin_id: int, current_fill_level: int, fill_rate_per_hour: float = 5.0):
        hours = self.predict_overflow_time(current_fill_level, fill_rate_per_hour)
        trend = "Rising" if current_fill_level >= 70 else "Moderate" if current_fill_level >= 40 else "Low"
        return {
            "bin_id": bin_id,
            "trend": trend,
            "est_hours_to_95pct": hours if hours != float("inf") else None,
        }


predictor = OverflowPredictor()
