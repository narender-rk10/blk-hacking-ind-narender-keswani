"""Efficient O(log n) period matching using sorted lists + bisect.

Optimized: float timestamps for comparisons, max() instead of sorted(),
datetime.fromisoformat() with dateutil fallback.
"""

from bisect import bisect_right
from typing import List, Optional
from datetime import datetime


def parse_dt(s) -> datetime:
    """Fast date parsing — fromisoformat handles '%Y-%m-%d %H:%M:%S' natively."""
    if isinstance(s, datetime):
        return s
    try:
        return datetime.fromisoformat(str(s))
    except (ValueError, TypeError):
        from dateutil import parser as dateutil_parser
        return dateutil_parser.parse(str(s))


def to_timestamp(s) -> float:
    """Parse a date string directly to a float timestamp."""
    return parse_dt(s).timestamp()


class PeriodMatcher:
    """
    Efficient period matching using sorted lists + bisect + float timestamps.

    Preprocessing: O(n log n)
    Query per transaction: O(log n + matches)
    All comparisons use float timestamps (faster than datetime).
    """

    def __init__(self, periods: list, key_field: str = None):
        for idx, p in enumerate(periods):
            p["_idx"] = idx
            p["_start_dt"] = parse_dt(p["start"])
            p["_end_dt"] = parse_dt(p["end"])
            p["_start_ts"] = p["_start_dt"].timestamp()
            p["_end_ts"] = p["_end_dt"].timestamp()

        self.periods = sorted(periods, key=lambda p: p["_start_ts"])
        self.starts_ts = [p["_start_ts"] for p in self.periods]

    def find_matching_ts(self, ts: float) -> List[dict]:
        """Find all periods containing timestamp ts (inclusive). O(log n + matches)."""
        idx = bisect_right(self.starts_ts, ts)
        return [self.periods[i] for i in range(idx) if self.periods[i]["_end_ts"] >= ts]

    def find_latest_start_match_ts(self, ts: float) -> Optional[dict]:
        """For q periods: matching period with latest start. O(log n + m) using max()."""
        matches = self.find_matching_ts(ts)
        if not matches:
            return None
        return max(matches, key=lambda p: (p["_start_ts"], -p["_idx"]))

    def find_all_matches_ts(self, ts: float) -> List[dict]:
        """For p periods: all matching periods (extras accumulate)."""
        return self.find_matching_ts(ts)

    # Backward-compatible datetime API
    def find_matching(self, dt: datetime) -> List[dict]:
        return self.find_matching_ts(dt.timestamp())

    def find_latest_start_match(self, dt: datetime) -> Optional[dict]:
        return self.find_latest_start_match_ts(dt.timestamp())

    def find_all_matches(self, dt: datetime) -> List[dict]:
        return self.find_matching_ts(dt.timestamp())
