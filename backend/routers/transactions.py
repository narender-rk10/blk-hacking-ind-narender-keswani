"""Transaction API endpoints."""

from fastapi import APIRouter, Request
from services.transaction_service import parse_expenses
from services.validator_service import validate_transactions
from services.filter_service import apply_temporal_filters
from datetime import datetime

router = APIRouter(tags=["Transactions"])


@router.post("/transactions:parse")
async def parse_transactions(request: Request):
    """
    Transaction Builder — Parse expenses into enriched transactions.

    Input: [{date, amount}, ...] OR { expenses: [{date, amount}, ...] }
    Output: [{date, amount, ceiling, remanent}, ...]
    """
    body = await request.json()
    if isinstance(body, list):
        expenses_raw = body
    else:
        expenses_raw = body.get("expenses", [])
    transactions = parse_expenses(expenses_raw)
    return transactions


@router.post("/transactions:validator")
async def validate(payload: dict):
    """
    Transaction Validator — Validate transactions based on wage.

    Input: { wage, transactions: [{date, amount, ceiling, remanent}, ...] }
    Output: { valid: [...], invalid: [...] }
    """
    wage = payload.get("wage", 0)
    transactions = payload.get("transactions", [])
    result = validate_transactions(wage, transactions)
    return result


@router.post("/transactions:filter")
async def filter_transactions(payload: dict):
    """
    Temporal Constraints Validator — Apply q, p, k filters.

    Input: { q, p, k, wage, transactions }
    Output: { valid: [...], invalid: [{...message}], k_results: [...] }
    """
    q = payload.get("q", [])
    p = payload.get("p", [])
    k = payload.get("k", [])
    transactions = payload.get("transactions", [])

    # Auto-parse raw expenses if ceiling/remanent not present
    if transactions and "ceiling" not in transactions[0]:
        transactions = parse_expenses(transactions)

    # Validate transactions first — separate valid from invalid
    valid_txns = []
    invalid_txns = []
    for txn in transactions:
        date_str = txn.get("date", "")
        errors = []
        try:
            datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            try:
                from dateutil import parser as dateutil_parser
                dateutil_parser.parse(date_str)
            except Exception:
                errors.append("Invalid date format")

        amount = txn.get("amount", 0)
        if amount < 0:
            errors.append("Amount must be non-negative")
        if amount >= 500000:
            errors.append("Amount exceeds maximum (500000)")

        if errors:
            invalid_txns.append({**txn, "message": "; ".join(errors)})
        else:
            valid_txns.append(txn)

    # Apply temporal filters only on valid transactions
    result = apply_temporal_filters(valid_txns, q, p, k)

    return {
        "valid": result.get("processed_transactions", []),
        "invalid": invalid_txns,
        "k_results": result.get("k_results", []),
    }
