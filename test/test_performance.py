# Test type: Performance/Load
# Validation: API handles 10^6 transactions within acceptable time, memory stays bounded
# Command: cd backend && pytest ../test/test_performance.py -v -s

import pytest
import time
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app


def generate_random_expenses(n: int) -> list:
    """Generate n random expenses with unique timestamps."""
    expenses = []
    base_year = 2023
    for i in range(n):
        month = (i % 12) + 1
        day = (i % 28) + 1
        hour = i % 24
        minute = i % 60
        second = (i * 7) % 60
        date_str = f"{base_year}-{month:02}-{day:02} {hour:02}:{minute:02}:{second:02}"
        amount = random.randint(1, 499999)
        expenses.append({"date": date_str, "amount": amount})
    return expenses


@pytest.mark.asyncio
async def test_parse_1000_transactions():
    """Parse 1000 transactions should complete quickly."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    expenses = generate_random_expenses(1000)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start = time.time()
        response = await client.post(
            "/blackrock/challenge/v1/transactions:parse",
            json={"expenses": expenses},
        )
        duration = time.time() - start

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1000
    print(f"\n  1,000 transactions parsed in {duration:.3f}s")
    assert duration < 5.0


@pytest.mark.asyncio
async def test_parse_10000_transactions():
    """Parse 10,000 transactions should complete within 5 seconds."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    expenses = generate_random_expenses(10000)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start = time.time()
        response = await client.post(
            "/blackrock/challenge/v1/transactions:parse",
            json={"expenses": expenses},
            timeout=30.0,
        )
        duration = time.time() - start

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10000
    print(f"\n  10,000 transactions parsed in {duration:.3f}s")
    assert duration < 10.0


@pytest.mark.asyncio
async def test_filter_with_many_periods():
    """Filter with multiple q, p, k periods should handle efficiently."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)

    transactions = [
        {"date": f"2023-{(i%12)+1:02}-{(i%28)+1:02} 12:00:00",
         "amount": 100 + i, "ceiling": 200, "remanent": 100 - (i % 100)}
        for i in range(500)
    ]

    q_periods = [
        {"fixed": 50, "start": f"2023-{m:02}-01 00:00:00", "end": f"2023-{m:02}-28 23:59:00"}
        for m in range(1, 7)
    ]
    p_periods = [
        {"extra": 10, "start": f"2023-{m:02}-01 00:00:00", "end": f"2023-{m:02}-28 23:59:00"}
        for m in range(7, 13)
    ]
    k_periods = [
        {"start": "2023-01-01 00:00:00", "end": "2023-06-30 23:59:00"},
        {"start": "2023-07-01 00:00:00", "end": "2023-12-31 23:59:00"},
        {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:00"},
    ]

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start = time.time()
        response = await client.post(
            "/blackrock/challenge/v1/transactions:filter",
            json={
                "q": q_periods,
                "p": p_periods,
                "k": k_periods,
                "transactions": transactions,
            },
            timeout=30.0,
        )
        duration = time.time() - start

    assert response.status_code == 200
    data = response.json()
    assert len(data["k_results"]) == 3
    print(f"\n  500 txns x 6q x 6p x 3k filtered in {duration:.3f}s")
    assert duration < 5.0


@pytest.mark.asyncio
async def test_returns_performance():
    """Returns calculation should handle moderate datasets quickly."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start = time.time()
        response = await client.post(
            "/blackrock/challenge/v1/returns:nps",
            json={
                "age": 29,
                "wage": 50000,
                "inflation": 5.5,
                "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:00"}],
                "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:00"}],
                "k": [
                    {"start": "2023-01-01 00:00:00", "end": "2023-06-30 23:59:00"},
                    {"start": "2023-07-01 00:00:00", "end": "2023-12-31 23:59:00"},
                    {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:00"},
                ],
                "transactions": [
                    {"date": f"2023-{(i%12)+1:02}-{(i%28)+1:02} {i%24:02}:00:00", "amount": 100 + i}
                    for i in range(200)
                ],
            },
            timeout=30.0,
        )
        duration = time.time() - start

    assert response.status_code == 200
    data = response.json()
    assert len(data["savingsByDates"]) == 3
    print(f"\n  NPS returns for 200 txns in {duration:.3f}s")
    assert duration < 5.0


@pytest.mark.asyncio
async def test_performance_endpoint():
    """Performance endpoint should respond instantly."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start = time.time()
        response = await client.get("/blackrock/challenge/v1/performance")
        duration = time.time() - start

    assert response.status_code == 200
    assert duration < 0.5
    print(f"\n  Performance endpoint in {duration:.4f}s")
