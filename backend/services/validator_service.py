"""Validation pipeline for transactions. Optimized: fromisoformat, batch isinstance."""

from datetime import datetime
from core.config import settings


def validate_transactions(wage: float, transactions: list) -> dict:
    """
    Validate transactions based on business rules.

    Checks: valid date, amount non-negative, amount < 500000, no duplicates,
    remanent non-negative, ceiling >= amount.
    """
    valid = []
    invalid = []
    seen_dates = set()

    if not transactions:
        return {"valid": valid, "invalid": invalid}

    # Batch type check — once per list, not per item
    is_dict = isinstance(transactions[0], dict)

    for txn in transactions:
        if is_dict:
            date_str = txn.get("date", "")
            amount = txn.get("amount", 0)
            ceiling = txn.get("ceiling", 0)
            remanent = txn.get("remanent", 0)
        else:
            date_str = getattr(txn, "date", "")
            amount = getattr(txn, "amount", 0)
            ceiling = getattr(txn, "ceiling", 0)
            remanent = getattr(txn, "remanent", 0)

        errors = []

        # Fast date validation
        try:
            dt = datetime.fromisoformat(str(date_str))
            date_str = dt.strftime(settings.DATE_FORMAT)
        except (ValueError, TypeError):
            try:
                from dateutil import parser as dateutil_parser
                dt = dateutil_parser.parse(str(date_str))
                date_str = dt.strftime(settings.DATE_FORMAT)
            except Exception:
                errors.append("Invalid date format")

        if amount < 0:
            errors.append("Amount must be non-negative")
        if amount >= 500000:
            errors.append("Amount exceeds maximum limit (500000)")
        if ceiling < amount:
            errors.append("Ceiling must be >= amount")
        if remanent < 0:
            errors.append("Remanent must be non-negative")

        if date_str in seen_dates:
            errors.append("Duplicate transaction date")
        seen_dates.add(date_str)

        txn_out = {
            "date": date_str,
            "amount": amount,
            "ceiling": ceiling,
            "remanent": remanent,
        }

        if errors:
            txn_out["message"] = "; ".join(errors)
            invalid.append(txn_out)
        else:
            valid.append(txn_out)

    return {"valid": valid, "invalid": invalid}
