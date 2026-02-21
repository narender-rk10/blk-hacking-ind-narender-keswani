"""
Synthetic Data Generator for BlackRock Auto-Savings API Testing.

Generates realistic financial transaction datasets at multiple scales:
  - small:  100 transactions, 3 q/p periods, 2 k periods
  - medium: 10,000 transactions, 12 q/p periods, 6 k periods
  - large:  100,000 transactions, 50 q/p periods, 12 k periods
  - stress: 1,000,000 transactions, 100 q/p periods, 24 k periods

Usage:
  python generate_synthetic_data.py                  # generates all sizes
  python generate_synthetic_data.py small             # generates only small
  python generate_synthetic_data.py medium large      # generates medium + large

Output:
  test/data/small_expenses.json
  test/data/small_full.json        (includes q, p, k, age, wage, inflation)
  test/data/medium_expenses.json
  test/data/medium_full.json
  ...etc

Command: python test/generate_synthetic_data.py [small|medium|large|stress]
"""

import json
import os
import random
import sys
from datetime import datetime, timedelta

random.seed(42)  # Reproducible datasets

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")

# -------------------------------------------------------------------
# Configuration for each dataset size
# -------------------------------------------------------------------
CONFIGS = {
    "small": {
        "n_transactions": 100,
        "n_q": 3,
        "n_p": 3,
        "n_k": 2,
        "year": 2023,
        "age": 29,
        "wage": 50000,
        "inflation": 5.5,
        "amount_range": (50, 10000),
        "fixed_range": (0, 500),
        "extra_range": (10, 100),
    },
    "medium": {
        "n_transactions": 10_000,
        "n_q": 12,
        "n_p": 12,
        "n_k": 6,
        "year": 2023,
        "age": 35,
        "wage": 75000,
        "inflation": 6.0,
        "amount_range": (10, 50000),
        "fixed_range": (0, 2000),
        "extra_range": (5, 500),
    },
    "large": {
        "n_transactions": 100_000,
        "n_q": 50,
        "n_p": 50,
        "n_k": 12,
        "year": 2023,
        "age": 40,
        "wage": 100000,
        "inflation": 5.0,
        "amount_range": (1, 100000),
        "fixed_range": (0, 5000),
        "extra_range": (1, 1000),
    },
    "stress": {
        "n_transactions": 1_000_000,
        "n_q": 100,
        "n_p": 100,
        "n_k": 24,
        "year": 2023,
        "age": 25,
        "wage": 60000,
        "inflation": 7.0,
        "amount_range": (1, 499999),
        "fixed_range": (0, 10000),
        "extra_range": (1, 5000),
    },
}


def generate_unique_timestamps(n: int, year: int) -> list:
    """Generate n unique timestamps spread across the given year."""
    start = datetime(year, 1, 1, 0, 0, 0)
    end = datetime(year, 12, 31, 23, 59, 59)
    total_seconds = int((end - start).total_seconds())

    # Pick n unique offsets
    if n > total_seconds:
        raise ValueError(f"Cannot generate {n} unique timestamps in one year")

    offsets = random.sample(range(total_seconds), n)
    offsets.sort()

    timestamps = []
    for offset in offsets:
        dt = start + timedelta(seconds=offset)
        timestamps.append(dt.strftime("%Y-%m-%d %H:%M:%S"))

    return timestamps


def generate_expenses(n: int, year: int, amount_range: tuple) -> list:
    """Generate n expense objects with unique timestamps."""
    timestamps = generate_unique_timestamps(n, year)
    expenses = []
    for ts in timestamps:
        amount = round(random.uniform(amount_range[0], amount_range[1]), 2)
        expenses.append({"date": ts, "amount": amount})
    return expenses


def generate_periods(n: int, year: int, period_type: str, value_range: tuple) -> list:
    """
    Generate n period objects (q, p, or k).

    Each period spans a random window within the year.
    q periods have 'fixed', p periods have 'extra', k periods have neither.
    """
    periods = []
    start_base = datetime(year, 1, 1, 0, 0, 0)
    end_base = datetime(year, 12, 31, 23, 59, 59)
    year_seconds = int((end_base - start_base).total_seconds())

    for _ in range(n):
        # Random start within first 11 months, end at least 1 day after
        s_offset = random.randint(0, year_seconds - 86400)
        duration = random.randint(86400, min(86400 * 90, year_seconds - s_offset))  # 1-90 days
        e_offset = s_offset + duration

        start_dt = start_base + timedelta(seconds=s_offset)
        end_dt = start_base + timedelta(seconds=min(e_offset, year_seconds))

        period = {
            "start": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "end": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
        }

        if period_type == "q":
            period["fixed"] = round(random.uniform(value_range[0], value_range[1]), 2)
        elif period_type == "p":
            period["extra"] = round(random.uniform(value_range[0], value_range[1]), 2)
        # k periods have no extra field

        periods.append(period)

    return periods


def generate_parsed_transactions(expenses: list) -> list:
    """Convert expenses to parsed transactions (with ceiling/remanent)."""
    import math

    transactions = []
    for exp in expenses:
        amount = exp["amount"]
        if amount % 100 == 0:
            ceiling = amount
            remanent = 0.0
        else:
            ceiling = math.ceil(amount / 100) * 100
            remanent = round(ceiling - amount, 2)
        transactions.append({
            "date": exp["date"],
            "amount": round(amount, 2),
            "ceiling": round(ceiling, 2),
            "remanent": round(remanent, 2),
        })
    return transactions


def generate_dataset(name: str, config: dict):
    """Generate and save a complete dataset."""
    print(f"  Generating {name} dataset ({config['n_transactions']:,} transactions)...")

    # Generate raw expenses
    expenses = generate_expenses(
        config["n_transactions"],
        config["year"],
        config["amount_range"],
    )

    # Generate periods
    q_periods = generate_periods(config["n_q"], config["year"], "q", config["fixed_range"])
    p_periods = generate_periods(config["n_p"], config["year"], "p", config["extra_range"])
    k_periods = generate_periods(config["n_k"], config["year"], "k", (0, 0))

    # Pre-parsed transactions
    parsed_transactions = generate_parsed_transactions(expenses)

    # ----- Save expenses only (for /transactions:parse) -----
    expenses_path = os.path.join(OUTPUT_DIR, f"{name}_expenses.json")
    with open(expenses_path, "w") as f:
        json.dump(expenses, f, separators=(",", ":"))
    expenses_size = os.path.getsize(expenses_path)
    print(f"    {expenses_path} ({expenses_size / 1024 / 1024:.2f} MB)")

    # ----- Save parsed transactions (for /transactions:validator and :filter) -----
    parsed_path = os.path.join(OUTPUT_DIR, f"{name}_parsed.json")
    with open(parsed_path, "w") as f:
        json.dump(parsed_transactions, f, separators=(",", ":"))
    parsed_size = os.path.getsize(parsed_path)
    print(f"    {parsed_path} ({parsed_size / 1024 / 1024:.2f} MB)")

    # ----- Save full payload (for /returns:nps, /returns:index) -----
    full_payload = {
        "age": config["age"],
        "wage": config["wage"],
        "inflation": config["inflation"],
        "q": q_periods,
        "p": p_periods,
        "k": k_periods,
        "transactions": expenses,
    }
    full_path = os.path.join(OUTPUT_DIR, f"{name}_full.json")
    with open(full_path, "w") as f:
        json.dump(full_payload, f, separators=(",", ":"))
    full_size = os.path.getsize(full_path)
    print(f"    {full_path} ({full_size / 1024 / 1024:.2f} MB)")

    # ----- Save filter payload (for /transactions:filter) -----
    filter_payload = {
        "q": q_periods,
        "p": p_periods,
        "k": k_periods,
        "transactions": parsed_transactions,
    }
    filter_path = os.path.join(OUTPUT_DIR, f"{name}_filter.json")
    with open(filter_path, "w") as f:
        json.dump(filter_payload, f, separators=(",", ":"))
    filter_size = os.path.getsize(filter_path)
    print(f"    {filter_path} ({filter_size / 1024 / 1024:.2f} MB)")

    # ----- Save validator payload (for /transactions:validator) -----
    validator_payload = {
        "wage": config["wage"],
        "transactions": parsed_transactions,
    }
    validator_path = os.path.join(OUTPUT_DIR, f"{name}_validator.json")
    with open(validator_path, "w") as f:
        json.dump(validator_payload, f, separators=(",", ":"))
    validator_size = os.path.getsize(validator_path)
    print(f"    {validator_path} ({validator_size / 1024 / 1024:.2f} MB)")

    # ----- Summary -----
    total_mb = (expenses_size + parsed_size + full_size + filter_size + validator_size) / 1024 / 1024
    print(f"    Total: {total_mb:.2f} MB")
    print()

    return {
        "name": name,
        "transactions": config["n_transactions"],
        "q_periods": config["n_q"],
        "p_periods": config["n_p"],
        "k_periods": config["n_k"],
        "total_mb": round(total_mb, 2),
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Determine which datasets to generate
    requested = sys.argv[1:] if len(sys.argv) > 1 else list(CONFIGS.keys())
    valid = [r for r in requested if r in CONFIGS]
    if not valid:
        print(f"Unknown dataset(s): {requested}")
        print(f"Available: {list(CONFIGS.keys())}")
        sys.exit(1)

    print("=" * 60)
    print("BlackRock Auto-Savings — Synthetic Data Generator")
    print("=" * 60)
    print()

    summaries = []
    for name in valid:
        config = CONFIGS[name]
        summary = generate_dataset(name, config)
        summaries.append(summary)

    # Print summary table
    print("=" * 60)
    print(f"{'Dataset':<10} {'Txns':>12} {'Q':>6} {'P':>6} {'K':>6} {'Size':>10}")
    print("-" * 60)
    for s in summaries:
        print(f"{s['name']:<10} {s['transactions']:>12,} {s['q_periods']:>6} {s['p_periods']:>6} {s['k_periods']:>6} {s['total_mb']:>8.2f} MB")
    print("=" * 60)
    print()
    print("Files saved to:", os.path.abspath(OUTPUT_DIR))
    print()
    print("Usage examples:")
    print("  # Parse expenses")
    print('  curl -X POST http://localhost:5477/blackrock/challenge/v1/transactions:parse \\')
    print('    -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"expenses": <contents of {valid[0]}_expenses.json>}}\'')
    print()
    print("  # Full returns calculation")
    print('  curl -X POST http://localhost:5477/blackrock/challenge/v1/returns:nps \\')
    print('    -H "Content-Type: application/json" \\')
    print(f'    -d @test/data/{valid[0]}_full.json')


if __name__ == "__main__":
    main()
