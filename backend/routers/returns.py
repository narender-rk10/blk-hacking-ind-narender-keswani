"""Returns calculation API endpoints."""

from fastapi import APIRouter
from services.filter_service import apply_temporal_filters
from services.returns_service import (
    NPSStrategy,
    IndexFundStrategy,
    ReturnsCalculator,
)
from services.transaction_service import parse_expenses

router = APIRouter(tags=["Returns"])


def _process_returns(payload: dict, strategy_cls):
    """
    Common logic for NPS and Index Fund return calculations.

    Steps:
    1. Parse raw expenses if transactions don't have ceiling/remanent
    2. Apply q, p, k temporal filters
    3. Calculate returns for each k period
    """
    age = payload.get("age", 30)
    wage = payload.get("wage", 0)
    inflation = payload.get("inflation", 0)
    q = payload.get("q", [])
    p = payload.get("p", [])
    k = payload.get("k", [])
    transactions = payload.get("transactions", [])

    # If transactions don't have ceiling/remanent, parse them first
    if transactions and "ceiling" not in transactions[0]:
        transactions = parse_expenses(transactions)

    # Apply temporal filters
    filter_result = apply_temporal_filters(transactions, q, p, k)
    processed = filter_result["processed_transactions"]
    k_results = filter_result["k_results"]

    # Calculate totals from processed (valid) transactions
    total_amount = round(sum(t["amount"] for t in processed), 2)
    total_ceiling = round(sum(t["ceiling"] for t in processed), 2)

    # Annual income = monthly wage * 12
    annual_income = wage * 12

    # Calculate returns for each k period
    strategy = strategy_cls()
    calculator = ReturnsCalculator(strategy)
    savings_by_dates = calculator.calculate_for_k_periods(
        k_results, age, annual_income, inflation
    )

    return {
        "transactionsTotalAmount": total_amount,
        "transactionsTotalCeiling": total_ceiling,
        "savingsByDates": savings_by_dates,
    }


@router.post("/returns:nps")
async def calculate_nps(payload: dict):
    """
    NPS Returns — Calculate returns with National Pension Scheme.

    Rate: 7.11% compounded annually.
    Tax benefit: up to min(invested, 10% annual income, 200000).
    """
    return _process_returns(payload, NPSStrategy)


@router.post("/returns:index")
async def calculate_index(payload: dict):
    """
    Index Fund Returns — Calculate returns with NIFTY 50 Index Fund.

    Rate: 14.49% compounded annually.
    No tax benefits.
    """
    return _process_returns(payload, IndexFundStrategy)
