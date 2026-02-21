"""Pipeline Pattern — Transaction processing pipeline.

Optimized: fromisoformat fast path, concurrent chunk processing for large batches.
"""

import math
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
from core.config import settings

PARALLEL_THRESHOLD = 5000
MAX_WORKERS = 4


class TransactionPipeline:
    """
    Pipeline pattern: each step transforms the data.
    Steps: Parse -> Validate -> ApplyQ -> ApplyP -> GroupByK
    """

    def __init__(self):
        self.steps = []

    def add_step(self, step_fn):
        self.steps.append(step_fn)
        return self

    def execute(self, data):
        for step in self.steps:
            data = step(data)
        return data


def _parse_single(date_str, amount, multiple, date_format):
    """Parse a single expense — pure function for both serial and parallel paths."""
    try:
        dt = datetime.fromisoformat(str(date_str))
        normalized_date = dt.strftime(date_format)
    except (ValueError, TypeError):
        try:
            from dateutil import parser as dateutil_parser
            dt = dateutil_parser.parse(str(date_str))
            normalized_date = dt.strftime(date_format)
        except Exception:
            normalized_date = str(date_str)

    if amount % multiple == 0:
        ceiling = amount
        remanent = 0.0
    else:
        ceiling = math.ceil(amount / multiple) * multiple
        remanent = ceiling - amount

    return {
        "date": normalized_date,
        "amount": round(amount, 2),
        "ceiling": round(ceiling, 2),
        "remanent": round(remanent, 2),
    }


def _parse_chunk(chunk):
    """Parse a chunk of expense dicts. Used by ProcessPoolExecutor."""
    multiple = 100
    date_format = "%Y-%m-%d %H:%M:%S"
    results = []
    for exp in chunk:
        date_str = exp.get("date", "")
        amount = exp.get("amount", 0)
        results.append(_parse_single(date_str, amount, multiple, date_format))
    return results


def parse_expenses(expenses: list) -> list:
    """
    Parse raw expenses into transactions with ceiling and remanent.
    Uses ProcessPoolExecutor for batches > 5000 transactions.
    """
    multiple = settings.CEILING_MULTIPLE
    date_format = settings.DATE_FORMAT

    # Normalize to dicts
    expense_dicts = []
    for exp in expenses:
        if isinstance(exp, dict):
            expense_dicts.append(exp)
        else:
            expense_dicts.append({
                "date": getattr(exp, "date", ""),
                "amount": getattr(exp, "amount", 0),
            })

    n = len(expense_dicts)

    # Small batch: process inline
    if n < PARALLEL_THRESHOLD:
        results = []
        for exp in expense_dicts:
            results.append(_parse_single(
                exp.get("date", ""), exp.get("amount", 0), multiple, date_format
            ))
        return results

    # Large batch: parallel chunk processing
    chunk_size = max(1, n // MAX_WORKERS)
    chunks = [expense_dicts[i:i + chunk_size] for i in range(0, n, chunk_size)]

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        chunk_results = list(executor.map(_parse_chunk, chunks))

    return [txn for chunk in chunk_results for txn in chunk]
