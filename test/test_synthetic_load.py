# Test type: Load / Stress
# Validation: API handles synthetic datasets of increasing scale against live server
# Command: python test/test_synthetic_load.py [small|medium|large|stress]
#   Requires backend running on http://localhost:5477

"""
Load test runner using synthetic data files.

Tests each endpoint with pre-generated datasets and reports timing & status.
"""

import json
import os
import sys
import time
import requests

BASE_URL = os.getenv("API_URL", "http://localhost:5477")
API = f"{BASE_URL}/blackrock/challenge/v1"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TIMEOUT = 300  # 5 minute timeout for stress tests


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"  [SKIP] {filename} not found. Run generate_synthetic_data.py first.")
        return None
    start = time.time()
    with open(path, "r") as f:
        data = json.load(f)
    load_time = time.time() - start
    size_mb = os.path.getsize(path) / 1024 / 1024
    print(f"  Loaded {filename} ({size_mb:.2f} MB) in {load_time:.2f}s")
    return data


def test_endpoint(name, method, url, payload=None, expected_key=None):
    """Hit an endpoint and report status + timing."""
    print(f"  {name}...", end=" ", flush=True)
    try:
        start = time.time()
        if method == "GET":
            resp = requests.get(url, timeout=TIMEOUT)
        else:
            resp = requests.post(url, json=payload, timeout=TIMEOUT)
        duration = time.time() - start

        if resp.status_code == 200:
            data = resp.json()
            detail = ""
            if expected_key and isinstance(data, dict) and expected_key in data:
                val = data[expected_key]
                if isinstance(val, list):
                    detail = f" ({len(val)} items)"
                else:
                    detail = f" ({expected_key}={val})"
            elif isinstance(data, list):
                detail = f" ({len(data)} items)"
            print(f"OK  {duration:.3f}s{detail}")
            return True, duration
        else:
            print(f"FAIL  status={resp.status_code}  {duration:.3f}s")
            print(f"    Response: {resp.text[:200]}")
            return False, duration
    except requests.exceptions.Timeout:
        print(f"TIMEOUT (>{TIMEOUT}s)")
        return False, TIMEOUT
    except requests.exceptions.ConnectionError:
        print("CONNECTION REFUSED - is the backend running?")
        return False, 0
    except Exception as e:
        print(f"ERROR: {e}")
        return False, 0


def run_suite(dataset_name):
    """Run all endpoint tests for a given dataset size."""
    print(f"\n{'='*60}")
    print(f"  Dataset: {dataset_name.upper()}")
    print(f"{'='*60}")

    results = []

    # 1. Parse expenses
    expenses = load_json(f"{dataset_name}_expenses.json")
    if expenses:
        ok, dur = test_endpoint(
            f"POST /transactions:parse ({len(expenses):,} expenses)",
            "POST",
            f"{API}/transactions:parse",
            payload={"expenses": expenses},
        )
        results.append(("parse", ok, dur, len(expenses)))

    # 2. Validate transactions
    validator_data = load_json(f"{dataset_name}_validator.json")
    if validator_data:
        n = len(validator_data.get("transactions", []))
        ok, dur = test_endpoint(
            f"POST /transactions:validator ({n:,} txns)",
            "POST",
            f"{API}/transactions:validator",
            payload=validator_data,
            expected_key="valid",
        )
        results.append(("validator", ok, dur, n))

    # 3. Filter with q/p/k
    filter_data = load_json(f"{dataset_name}_filter.json")
    if filter_data:
        n = len(filter_data.get("transactions", []))
        nq = len(filter_data.get("q", []))
        np_ = len(filter_data.get("p", []))
        nk = len(filter_data.get("k", []))
        ok, dur = test_endpoint(
            f"POST /transactions:filter ({n:,} txns, {nq}q/{np_}p/{nk}k)",
            "POST",
            f"{API}/transactions:filter",
            payload=filter_data,
            expected_key="k_results",
        )
        results.append(("filter", ok, dur, n))

    # 4. NPS returns
    full_data = load_json(f"{dataset_name}_full.json")
    if full_data:
        n = len(full_data.get("transactions", []))
        ok, dur = test_endpoint(
            f"POST /returns:nps ({n:,} txns)",
            "POST",
            f"{API}/returns:nps",
            payload=full_data,
            expected_key="savingsByDates",
        )
        results.append(("nps", ok, dur, n))

    # 5. Index returns
    if full_data:
        ok, dur = test_endpoint(
            f"POST /returns:index ({n:,} txns)",
            "POST",
            f"{API}/returns:index",
            payload=full_data,
            expected_key="savingsByDates",
        )
        results.append(("index", ok, dur, n))

    # 6. Performance
    ok, dur = test_endpoint(
        "GET /performance",
        "GET",
        f"{API}/performance",
        expected_key="memory",
    )
    results.append(("performance", ok, dur, 0))

    # Summary
    print(f"\n  {'Endpoint':<20} {'Status':<8} {'Time':>10} {'Rows':>12}")
    print(f"  {'-'*52}")
    total_ok = 0
    total_dur = 0
    for name, ok, dur, n in results:
        status = "PASS" if ok else "FAIL"
        print(f"  {name:<20} {status:<8} {dur:>9.3f}s {n:>12,}")
        if ok:
            total_ok += 1
        total_dur += dur
    print(f"  {'-'*52}")
    print(f"  {total_ok}/{len(results)} passed, total time: {total_dur:.3f}s")

    return results


def main():
    # Check backend connectivity first
    print("Checking backend connectivity...")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            print(f"Backend OK: {BASE_URL}")
        else:
            print(f"Backend returned {r.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"Cannot connect to {BASE_URL}. Start the backend first.")
        sys.exit(1)

    # Determine which datasets to test
    requested = sys.argv[1:] if len(sys.argv) > 1 else ["small", "medium"]
    available = ["small", "medium", "large", "stress"]
    to_run = [r for r in requested if r in available]

    if not to_run:
        print(f"Unknown dataset(s). Available: {available}")
        sys.exit(1)

    all_results = {}
    for name in to_run:
        all_results[name] = run_suite(name)

    # Final summary
    print(f"\n{'='*60}")
    print("  FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"  {'Dataset':<10} {'Endpoints':<12} {'Total Time':>12} {'Status':>8}")
    print(f"  {'-'*44}")
    for name, results in all_results.items():
        passed = sum(1 for _, ok, _, _ in results if ok)
        total = len(results)
        total_time = sum(dur for _, _, dur, _ in results)
        status = "ALL PASS" if passed == total else f"{passed}/{total}"
        print(f"  {name:<10} {total:<12} {total_time:>11.3f}s {status:>8}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
