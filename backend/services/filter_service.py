"""Temporal constraints filtering — Optimized with timestamp caching + bisect k-grouping.

Key optimizations:
- Parse all dates ONCE into float timestamps before any loop
- Use float timestamp comparisons (not datetime objects)
- K-grouping: sort by timestamp + bisect for O(k log n) instead of O(n*k)
"""

from bisect import bisect_left, bisect_right
from datetime import datetime
from utils.interval_tree import PeriodMatcher, parse_dt


def _fast_parse_ts(s: str) -> float:
    """Parse date string to float timestamp. Fast path for ISO format."""
    try:
        return datetime.fromisoformat(s).timestamp()
    except (ValueError, TypeError):
        return parse_dt(s).timestamp()


def apply_temporal_filters(transactions: list, q: list, p: list, k: list) -> dict:
    """
    Apply q, p, k temporal filters to transactions.

    Complexity:
    - Date parsing: O(n) — each transaction parsed exactly once
    - Q matching: O(n * log q) per transaction via bisect
    - P matching: O(n * log p) per transaction via bisect
    - K grouping: O(n log n) sort + O(k log n) bisect queries
    """
    # --- Build period dicts ---
    q_periods = [
        {"fixed": qp.get("fixed", 0) if isinstance(qp, dict) else getattr(qp, "fixed", 0),
         "start": qp.get("start", "") if isinstance(qp, dict) else getattr(qp, "start", ""),
         "end": qp.get("end", "") if isinstance(qp, dict) else getattr(qp, "end", "")}
        for qp in q
    ]
    p_periods = [
        {"extra": pp.get("extra", 0) if isinstance(pp, dict) else getattr(pp, "extra", 0),
         "start": pp.get("start", "") if isinstance(pp, dict) else getattr(pp, "start", ""),
         "end": pp.get("end", "") if isinstance(pp, dict) else getattr(pp, "end", "")}
        for pp in p
    ]
    k_periods = [
        {"start": kp.get("start", "") if isinstance(kp, dict) else getattr(kp, "start", ""),
         "end": kp.get("end", "") if isinstance(kp, dict) else getattr(kp, "end", "")}
        for kp in k
    ]

    q_matcher = PeriodMatcher(q_periods) if q_periods else None
    p_matcher = PeriodMatcher(p_periods) if p_periods else None

    # --- Phase 1: Parse all transaction dates ONCE into timestamps ---
    n = len(transactions)
    txn_timestamps = [0.0] * n
    txn_dates = [""] * n
    txn_amounts = [0.0] * n
    txn_ceilings = [0.0] * n
    txn_remanents = [0.0] * n

    for i, txn in enumerate(transactions):
        date_str = txn.get("date", "")
        txn_dates[i] = date_str
        txn_amounts[i] = txn.get("amount", 0)
        txn_ceilings[i] = txn.get("ceiling", 0)
        txn_remanents[i] = txn.get("remanent", 0)
        try:
            txn_timestamps[i] = _fast_parse_ts(date_str)
        except Exception:
            txn_timestamps[i] = float("nan")

    # --- Phase 2: Apply q period rules (fixed override) ---
    if q_matcher:
        for i in range(n):
            ts = txn_timestamps[i]
            if ts != ts:  # NaN check
                continue
            q_match = q_matcher.find_latest_start_match_ts(ts)
            if q_match:
                txn_remanents[i] = q_match["fixed"]

    # --- Phase 3: Apply p period rules (extra addition) ---
    if p_matcher:
        for i in range(n):
            ts = txn_timestamps[i]
            if ts != ts:
                continue
            p_matches = p_matcher.find_all_matches_ts(ts)
            for pm in p_matches:
                txn_remanents[i] += pm["extra"]

    # --- Build processed output ---
    processed = [
        {
            "date": txn_dates[i],
            "amount": txn_amounts[i],
            "ceiling": txn_ceilings[i],
            "remanent": round(txn_remanents[i], 2),
        }
        for i in range(n)
    ]

    # --- Phase 4: K-grouping with sorted timestamps + bisect ---
    # Sort indices by timestamp for binary search
    sorted_indices = sorted(range(n), key=lambda i: txn_timestamps[i])
    sorted_ts = [txn_timestamps[i] for i in sorted_indices]
    sorted_remanents = [txn_remanents[i] for i in sorted_indices]

    # Prefix sum for O(1) range queries
    prefix = [0.0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + sorted_remanents[i]

    k_results = []
    for kp in k_periods:
        k_start_ts = _fast_parse_ts(kp["start"])
        k_end_ts = _fast_parse_ts(kp["end"])

        lo = bisect_left(sorted_ts, k_start_ts)
        hi = bisect_right(sorted_ts, k_end_ts)

        total = prefix[hi] - prefix[lo]

        k_results.append({
            "start": kp["start"],
            "end": kp["end"],
            "amount": round(total, 2),
        })

    return {
        "processed_transactions": processed,
        "k_results": k_results,
    }
